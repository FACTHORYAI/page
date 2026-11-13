#!/usr/bin/env python3
"""Check, before any build of a signing run, that the environment `release` holds every secret the
run signs and publishes with, and that each is well formed. A missing or broken value costs one
minute here instead of a macOS build. Only names reach the log, never a value.

What a run needs (bandpey-hq/github-infra, `signing/office-release.json` and the release
identities):

  macOS    APPLE_CERTIFICATE (base64 .p12) and APPLE_CERTIFICATE_PASSWORD: the file opens with its
           password, is not expired and holds a Developer ID Application identity of the team
           APPLE_TEAM_ID (97RCTA3838); APPLE_API_KEY (the App Store Connect key's id),
           APPLE_API_ISSUER (the issuer id) and APPLE_API_KEY_P8 (the .p8, as text or base64),
           which must parse as a private key. The temporary keychain's password is made by the
           job; there is no secret for it.
  Windows  AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_SIGNING_ENDPOINT, AZURE_SIGNING_ACCOUNT and
           AZURE_CERT_PROFILE, which name Bandpey GmbH's Artifact Signing account and profile.
           There is no client secret: the jobs sign in with GitHub's OIDC token.
  release  (a run that publishes) DOWNLOADS_TOKEN, and PACKAGES_GPG_KEY, which gpg must read as a
           key that can sign.

  python3 facthory/signing_preflight.py [--publish]

Reads the secrets from the environment; exits 1 naming every problem found.
"""

from __future__ import annotations

import base64
import binascii
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path

TEAM_ID = "97RCTA3838"
AZURE_ENDPOINT = "https://weu.codesigning.azure.net"
AZURE_ACCOUNT = "bandpey-signing"
AZURE_PROFILE = "bandpey-public"
UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
KEY_ID = re.compile(r"^[A-Z0-9]{10}$")


def run(args: list[str], stdin: bytes | None = None, env: Mapping[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, input=stdin, capture_output=True, check=False, env=dict(env) if env is not None else None)


def decode_p8(value: str) -> bytes | None:
    """The key's PEM: the secret as it is, or its base64."""
    text = value.strip()
    if "BEGIN" in text and "PRIVATE KEY" in text:
        return (text + "\n").encode()
    try:
        raw = base64.b64decode("".join(text.split()), validate=True)
    except (binascii.Error, ValueError):
        return None
    return raw if b"PRIVATE KEY" in raw else None


def check_apple(env: Mapping[str, str], problems: list[str], notes: list[str]) -> None:
    wanted = ["APPLE_CERTIFICATE", "APPLE_CERTIFICATE_PASSWORD", "APPLE_TEAM_ID", "APPLE_API_KEY", "APPLE_API_ISSUER", "APPLE_API_KEY_P8"]
    missing = [n for n in wanted if not env.get(n)]
    problems += [f"{n} is not set" for n in missing]
    if env.get("APPLE_TEAM_ID") and env["APPLE_TEAM_ID"] != TEAM_ID:
        problems.append("APPLE_TEAM_ID is not Bandpey GmbH's team")
    if env.get("APPLE_API_KEY") and not KEY_ID.match(env["APPLE_API_KEY"]):
        problems.append("APPLE_API_KEY is not an App Store Connect key id (10 letters and digits)")
    if env.get("APPLE_API_ISSUER") and not UUID.match(env["APPLE_API_ISSUER"]):
        problems.append("APPLE_API_ISSUER is not an issuer id (a UUID)")
    if env.get("APPLE_API_KEY_P8"):
        pem = decode_p8(env["APPLE_API_KEY_P8"])
        if pem is None or run(["openssl", "pkey", "-noout"], stdin=pem).returncode != 0:
            problems.append("APPLE_API_KEY_P8 is not a private key, as text or as base64")
        else:
            notes.append("APPLE_API_KEY_P8 parses as a private key")
    if env.get("APPLE_CERTIFICATE") and env.get("APPLE_CERTIFICATE_PASSWORD"):
        check_p12(env, problems, notes)


def check_p12(env: Mapping[str, str], problems: list[str], notes: list[str]) -> None:
    before = len(problems)
    try:
        p12 = base64.b64decode("".join(env["APPLE_CERTIFICATE"].split()), validate=True)
    except (binascii.Error, ValueError):
        problems.append("APPLE_CERTIFICATE is not base64")
        return
    # The password goes to openssl by the name of an environment variable, never in an argument.
    child = {**os.environ, "PREFLIGHT_P12_PASSWORD": env["APPLE_CERTIFICATE_PASSWORD"]}
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "identity.p12"
        path.write_bytes(p12)
        path.chmod(0o600)
        cert = None
        for legacy in ([], ["-legacy"]):  # older exports use algorithms openssl 3 asks for by name
            r = run(["openssl", "pkcs12", "-in", str(path), "-passin", "env:PREFLIGHT_P12_PASSWORD", "-nokeys", "-clcerts", *legacy], env=child)
            if r.returncode == 0 and b"BEGIN CERTIFICATE" in r.stdout:
                cert = r.stdout
                break
        if cert is None:
            problems.append("APPLE_CERTIFICATE does not open with APPLE_CERTIFICATE_PASSWORD")
            return
        info = run(["openssl", "x509", "-noout", "-subject", "-enddate", "-nameopt", "RFC2253"], stdin=cert)
        subject = info.stdout.decode(errors="replace")
        if "Developer ID Application" not in subject or f"({TEAM_ID})" not in subject:
            problems.append(f"APPLE_CERTIFICATE holds no Developer ID Application identity of team {TEAM_ID}")
        if run(["openssl", "x509", "-noout", "-checkend", "0"], stdin=cert).returncode != 0:
            problems.append("APPLE_CERTIFICATE's identity has expired")
        key = False
        for legacy in ([], ["-legacy"]):
            r = run(["openssl", "pkcs12", "-in", str(path), "-passin", "env:PREFLIGHT_P12_PASSWORD", "-nocerts", "-nodes", *legacy], env=child)
            if r.returncode == 0 and b"PRIVATE KEY" in r.stdout:
                key = True
                break
        if not key:
            problems.append("APPLE_CERTIFICATE holds no private key")
        ends = re.search(r"notAfter=(.*)", subject)
        if len(problems) == before:
            notes.append(f"APPLE_CERTIFICATE opens, is a Developer ID Application identity of team {TEAM_ID}" + (f", valid until {ends.group(1)}" if ends else ""))


def check_azure(env: Mapping[str, str], problems: list[str], notes: list[str]) -> None:
    wanted = ["AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_SIGNING_ENDPOINT", "AZURE_SIGNING_ACCOUNT", "AZURE_CERT_PROFILE"]
    problems += [f"{n} is not set" for n in wanted if not env.get(n)]
    for n in ("AZURE_TENANT_ID", "AZURE_CLIENT_ID"):
        if env.get(n) and not UUID.match(env[n]):
            problems.append(f"{n} is not a UUID")
    if env.get("AZURE_SIGNING_ENDPOINT") and env["AZURE_SIGNING_ENDPOINT"].rstrip("/") != AZURE_ENDPOINT:
        problems.append("AZURE_SIGNING_ENDPOINT is not Bandpey GmbH's signing endpoint (a wrong region answers 403)")
    if env.get("AZURE_SIGNING_ACCOUNT") and env["AZURE_SIGNING_ACCOUNT"] != AZURE_ACCOUNT:
        problems.append("AZURE_SIGNING_ACCOUNT is not Bandpey GmbH's signing account")
    if env.get("AZURE_CERT_PROFILE") and env["AZURE_CERT_PROFILE"] != AZURE_PROFILE:
        problems.append("AZURE_CERT_PROFILE is not Bandpey GmbH's public certificate profile")
    if not any(p.startswith("AZURE_") for p in problems):
        notes.append("the AZURE_* values are set and name the signing account and profile")


def check_publish(env: Mapping[str, str], problems: list[str], notes: list[str]) -> None:
    if not env.get("DOWNLOADS_TOKEN"):
        problems.append("DOWNLOADS_TOKEN is not set")
    key = env.get("PACKAGES_GPG_KEY")
    if not key:
        problems.append("PACKAGES_GPG_KEY is not set")
        return
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "gnupg"
        home.mkdir(mode=0o700)
        r = run(["gpg", "--batch", "--homedir", str(home), "--show-keys", "--with-colons"], stdin=(key + "\n").encode())
        out = r.stdout.decode(errors="replace")
        # A secret key record whose capabilities (field 12) include signing.
        if r.returncode != 0 or not any(line.startswith("sec:") and "s" in line.split(":")[11].lower() for line in out.splitlines() if len(line.split(":")) > 11):
            problems.append("PACKAGES_GPG_KEY is not a secret key that can sign")
        else:
            notes.append("PACKAGES_GPG_KEY is a secret key that can sign")


def check(env: Mapping[str, str], publish: bool) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    notes: list[str] = []
    check_apple(env, problems, notes)
    check_azure(env, problems, notes)
    if publish:
        check_publish(env, problems, notes)
    return problems, notes


def main() -> int:
    publish = "--publish" in sys.argv[1:]
    problems, notes = check(os.environ, publish)
    for n in notes:
        print(f"ok: {n}")
    for p in problems:
        print(f"::error::The environment release: {p}")
    if problems:
        print(f"signing preflight: {len(problems)} problem(s); nothing was built", file=sys.stderr)
        return 1
    print("signing preflight: every secret this run signs and publishes with is set and well formed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

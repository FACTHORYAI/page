#!/usr/bin/env python3
"""Tests of signing_preflight.py with throwaway identities made here: a self-signed certificate
with a Developer ID Application name, a P-256 key as the App Store Connect key, a gpg key.

  env -i PATH="$PATH" HOME="$HOME" python3 facthory/test_signing_preflight.py
"""

from __future__ import annotations

import base64
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import signing_preflight as sp  # noqa: E402

PASSWORD = "p12 pass #1 $x"
GOOD_AZURE = {
    "AZURE_TENANT_ID": "16b3a288-2a37-4dd1-8081-bb81ddf6de00",
    "AZURE_CLIENT_ID": "11111111-2222-3333-4444-555555555555",
    "AZURE_SIGNING_ENDPOINT": "https://weu.codesigning.azure.net",
    "AZURE_SIGNING_ACCOUNT": "bandpey-signing",
    "AZURE_CERT_PROFILE": "bandpey-public",
}


def sh(*args: str, cwd: Path, stdin: str | None = None) -> str:
    return subprocess.run(args, cwd=cwd, input=stdin, capture_output=True, text=True, check=True).stdout


def make_p12(tmp: Path, subject: str, days: int = 30, password: str = PASSWORD) -> str:
    sh("openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", "k.pem", "-out", "c.pem", "-days", str(days), "-subj", subject, cwd=tmp)
    sh("openssl", "pkcs12", "-export", "-inkey", "k.pem", "-in", "c.pem", "-out", "i.p12", "-passout", f"pass:{password}", cwd=tmp)
    return base64.b64encode((tmp / "i.p12").read_bytes()).decode()


class Preflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = Path(tempfile.mkdtemp())
        cls.good_p12 = make_p12(cls.tmp, f"/CN=Developer ID Application: Bandpey GmbH ({sp.TEAM_ID})/O=Bandpey GmbH")
        sh("openssl", "ecparam", "-name", "prime256v1", "-genkey", "-noout", "-out", "ec.pem", cwd=cls.tmp)
        sh("openssl", "pkcs8", "-topk8", "-nocrypt", "-in", "ec.pem", "-out", "AuthKey.p8", cwd=cls.tmp)
        cls.p8 = (cls.tmp / "AuthKey.p8").read_text()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def apple(self, **over: str) -> dict[str, str]:
        env = {
            "APPLE_CERTIFICATE": self.good_p12, "APPLE_CERTIFICATE_PASSWORD": PASSWORD, "APPLE_TEAM_ID": sp.TEAM_ID,
            "APPLE_API_KEY": "ABCDE12345", "APPLE_API_ISSUER": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "APPLE_API_KEY_P8": self.p8,
        }
        env.update(over)
        return env

    def problems(self, env: dict[str, str], publish: bool = False) -> list[str]:
        return sp.check({**GOOD_AZURE, **env}, publish)[0]

    def test_everything_good_passes(self) -> None:
        problems, notes = sp.check({**GOOD_AZURE, **self.apple()}, False)
        self.assertEqual(problems, [])
        self.assertTrue(any("Developer ID Application" in n for n in notes))

    def test_p8_as_base64_passes(self) -> None:
        self.assertEqual(self.problems(self.apple(APPLE_API_KEY_P8=base64.b64encode(self.p8.encode()).decode())), [])

    def test_missing_names_are_listed_by_name_only(self) -> None:
        problems, _ = sp.check({}, False)
        self.assertIn("APPLE_CERTIFICATE is not set", problems)
        self.assertIn("AZURE_CLIENT_ID is not set", problems)
        self.assertEqual(len(problems), 11)

    def test_wrong_password_and_wrong_team_and_no_developer_id(self) -> None:
        self.assertIn("APPLE_CERTIFICATE does not open with APPLE_CERTIFICATE_PASSWORD", self.problems(self.apple(APPLE_CERTIFICATE_PASSWORD="nope")))
        other = make_p12(self.tmp, "/CN=Developer ID Application: Someone Else (ZZZZZZZZZZ)")
        self.assertTrue(any("Developer ID Application identity of team" in p for p in self.problems(self.apple(APPLE_CERTIFICATE=other))))
        plain = make_p12(self.tmp, "/CN=Not a signing identity")
        self.assertTrue(any("Developer ID Application identity of team" in p for p in self.problems(self.apple(APPLE_CERTIFICATE=plain))))
        self.assertIn("APPLE_TEAM_ID is not Bandpey GmbH's team", self.problems(self.apple(APPLE_TEAM_ID="AAAAAAAAAA")))

    def test_not_base64_certificate(self) -> None:
        self.assertIn("APPLE_CERTIFICATE is not base64", self.problems(self.apple(APPLE_CERTIFICATE="not base64 !!")))

    def test_notary_key_must_parse(self) -> None:
        self.assertTrue(any("APPLE_API_KEY_P8" in p for p in self.problems(self.apple(APPLE_API_KEY_P8="hello"))))
        self.assertTrue(any("APPLE_API_KEY is not" in p for p in self.problems(self.apple(APPLE_API_KEY="short"))))
        self.assertTrue(any("APPLE_API_ISSUER" in p for p in self.problems(self.apple(APPLE_API_ISSUER="x"))))

    def test_azure_values(self) -> None:
        bad = {**GOOD_AZURE, "AZURE_SIGNING_ENDPOINT": "https://eus.codesigning.azure.net", "AZURE_CLIENT_ID": "x"}
        problems = sp.check({**self.apple(), **bad}, False)[0]
        self.assertEqual(len(problems), 2)
        self.assertEqual(sp.check({**self.apple(), **GOOD_AZURE, "AZURE_SIGNING_ENDPOINT": "https://weu.codesigning.azure.net/"}, False)[0], [])

    @unittest.skipUnless(shutil.which("gpg"), "gpg is not installed")
    def test_publish_needs_a_token_and_a_signing_key(self) -> None:
        home = self.tmp / "gnupg"
        home.mkdir(mode=0o700, exist_ok=True)
        sh("gpg", "--batch", "--homedir", str(home), "--passphrase", "", "--pinentry-mode", "loopback", "--quick-generate-key", "test <t@example.invalid>", "rsa2048", "sign", "never", cwd=self.tmp)
        key = sh("gpg", "--batch", "--homedir", str(home), "--armor", "--export-secret-keys", cwd=self.tmp)
        env = {**GOOD_AZURE, **self.apple(), "DOWNLOADS_TOKEN": "t", "PACKAGES_GPG_KEY": key}
        self.assertEqual(sp.check(env, True)[0], [])
        self.assertEqual(sp.check(env, False)[0], [])
        self.assertEqual(sp.check({**env, "PACKAGES_GPG_KEY": "garbage"}, True)[0], ["PACKAGES_GPG_KEY is not a secret key that can sign"])
        self.assertEqual(sp.check({k: v for k, v in env.items() if k != "DOWNLOADS_TOKEN"}, True)[0], ["DOWNLOADS_TOKEN is not set"])


if __name__ == "__main__":
    unittest.main()

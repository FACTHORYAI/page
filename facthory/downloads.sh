#!/usr/bin/env bash
# Serves our releases from https://downloads.facthory.com (FACTHORYAI/platform#101): a Cloudflare
# R2 bucket in the EU, written over its S3 API with DOWNLOADS_TOKEN, a token for this bucket only
# (the environment release). The app is this repository's name.
#
#   bash facthory/downloads.sh release v<version>   the published release's files, then the feed
#   bash facthory/downloads.sh feed                 the feed alone, after a halt or a resume
#
# A version's files go to releases/<app>/<version>/<file>, cached for a year. The bucket takes
# each of them once and never changes it: a re-run skips a file whose SHA-256 (kept as its sha256
# metadata) matches, and fails on one that differs. They come from the published GitHub release,
# so a re-run that rebuilt the files still serves what was published.
#
# The feed, feeds/<app>/latest.json, is the latest release's latest.json (facthory/release.py),
# cached for 60 seconds and written last. When no release is the latest (the only one is halted,
# facthory-rollout.yml), it is the newest release's with rollout 0, which no copy takes.
set -euo pipefail

ACCOUNT=e36198fb635c4cfa763367d230fe532b
BUCKET=facthory-downloads
HOST=https://downloads.facthory.com
APP=${GITHUB_REPOSITORY##*/}

# The S3 credentials of the token: its id, and the SHA-256 of its value.
credentials() {
  : "${DOWNLOADS_TOKEN:?DOWNLOADS_TOKEN is not set: it is a secret of the environment release}"
  local id
  id=$(curl -fsS -H "Authorization: Bearer ${DOWNLOADS_TOKEN}" \
    "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT}/tokens/verify" | jq -r '.result.id // empty')
  if [ -z "$id" ]; then
    echo "::error::Cloudflare doesn't accept DOWNLOADS_TOKEN." >&2
    return 1
  fi
  AWS_SECRET_ACCESS_KEY=$(printf '%s' "$DOWNLOADS_TOKEN" | sha256sum | cut -d' ' -f1)
  echo "::add-mask::${AWS_SECRET_ACCESS_KEY}"
  export AWS_ACCESS_KEY_ID=$id AWS_SECRET_ACCESS_KEY AWS_DEFAULT_REGION=auto
  # The bucket's EU endpoint; R2 rejects the checksums newer aws-cli sends by default.
  export AWS_ENDPOINT_URL="https://${ACCOUNT}.eu.r2.cloudflarestorage.com"
  export AWS_REQUEST_CHECKSUM_CALCULATION=when_required AWS_RESPONSE_CHECKSUM_VALIDATION=when_required
}

content_type() {
  case "$1" in
    *.dmg) echo application/x-apple-diskimage ;;
    *.msi) echo application/x-msi ;;
    *.zip) echo application/zip ;;
    *.AppImage) echo application/vnd.appimage ;;
    *.zsync) echo application/x-zsync ;;
    *.deb) echo application/vnd.debian.binary-package ;;
    *.rpm) echo application/x-rpm ;;
    *.tar.gz) echo application/gzip ;;
    *.flatpak) echo application/vnd.flatpak ;;
    *.json) echo application/json ;;
    SHA256SUMS) echo "text/plain; charset=utf-8" ;;
    *) echo application/octet-stream ;;
  esac
}

# put_once <file> <key>: a version's file, written once.
put_once() {
  local file=$1 key=$2 sum there err
  sum=$(sha256sum "$file" | cut -d' ' -f1)
  err=$(mktemp)
  if there=$(aws s3api head-object --bucket "$BUCKET" --key "$key" --query 'Metadata.sha256' --output text 2>"$err"); then
    if [ "$there" = "$sum" ]; then
      echo "${key}: already served"
      return 0
    fi
    echo "::error::${key} is already served with another SHA-256 (${there}, this one ${sum}), and it can't change. Release a new version." >&2
    return 1
  fi
  if ! grep -q -E '\(404\)|Not Found' "$err"; then
    echo "::error::Couldn't look up ${key}: $(tail -n 1 "$err")" >&2
    return 1
  fi
  aws s3 cp "$file" "s3://${BUCKET}/${key}" --only-show-errors --metadata "sha256=${sum}" \
    --cache-control "public, max-age=31536000, immutable" --content-type "$(content_type "${file##*/}")"
  echo "${key}: uploaded"
}

feed() {
  local tag dir offers
  dir=$(mktemp -d)
  # The latest release: published, and neither a draft nor halted (a pre-release).
  tag=$(gh release view --repo "$GITHUB_REPOSITORY" --json tagName --jq .tagName 2>/dev/null || true)
  if [ -n "$tag" ]; then
    gh release download "$tag" --repo "$GITHUB_REPOSITORY" --pattern latest.json --dir "$dir"
    offers="offers ${tag}"
  else
    tag=$(gh release list --repo "$GITHUB_REPOSITORY" --exclude-drafts --limit 1 --json tagName --jq '.[0].tagName // ""')
    if [ -z "$tag" ]; then
      echo "No release yet, so no feed."
      return 0
    fi
    gh release download "$tag" --repo "$GITHUB_REPOSITORY" --pattern latest.json --dir "$dir"
    jq '.rollout = 0' "$dir/latest.json" >"$dir/halted.json"
    mv "$dir/halted.json" "$dir/latest.json"
    offers="names ${tag}, halted, and offers it to no copy"
  fi
  aws s3 cp "$dir/latest.json" "s3://${BUCKET}/feeds/${APP}/latest.json" --only-show-errors \
    --cache-control "public, max-age=60" --content-type application/json
  echo "The feed ${HOST}/feeds/${APP}/latest.json ${offers}." | tee -a "${GITHUB_STEP_SUMMARY:-/dev/null}"
}

release() {
  local tag=$1 dir file
  dir=$(mktemp -d)
  gh release download "$tag" --repo "$GITHUB_REPOSITORY" --dir "$dir"
  (cd "$dir" && sha256sum --quiet -c SHA256SUMS)
  for file in "$dir"/*; do
    [ "${file##*/}" = latest.json ] && continue
    put_once "$file" "releases/${APP}/${tag#v}/${file##*/}"
  done
  feed
}

case "${1:-}" in
  release)
    [[ "${2:-}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "usage: $0 release v<version>" >&2; exit 2; }
    credentials
    release "$2"
    ;;
  feed)
    credentials
    feed
    ;;
  *)
    echo "usage: $0 release v<version> | feed" >&2
    exit 2
    ;;
esac

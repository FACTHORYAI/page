#!/usr/bin/env bash
# Print the commit that tag $1 of $GITHUB_REPOSITORY points at (an annotated tag is followed to
# its commit), or nothing when the repository has no such tag. Any other answer from the API, an
# outage or a refused token, exits non-zero: the release jobs must never read an error as "no
# tag". Needs gh and GH_TOKEN. Used by facthory-release.yml.
set -euo pipefail
tag=$1
if ! out=$(gh api "repos/${GITHUB_REPOSITORY}/git/ref/tags/${tag}" --jq '.object.type + " " + .object.sha' 2>&1); then
  case $out in
    *"(HTTP 404)"*) exit 0 ;;
    *) echo "::error::Could not look up tag ${tag}: ${out}" >&2; exit 1 ;;
  esac
fi
read -r type sha <<<"$out"
while [ "$type" = tag ]; do
  out=$(gh api "repos/${GITHUB_REPOSITORY}/git/tags/${sha}" --jq '.object.type + " " + .object.sha')
  read -r type sha <<<"$out"
done
if [ "$type" != commit ]; then
  echo "::error::Tag ${tag} points at a ${type}, not a commit." >&2
  exit 1
fi
echo "$sha"

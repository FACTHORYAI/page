#!/usr/bin/env bash
# Print the commit that tag $1 of $GITHUB_REPOSITORY points at (an annotated tag is followed to
# its commit), or nothing when the repository has no such tag. matching-refs answers a missing
# tag with an empty list, so any failed request (an outage, a refused token, a missing
# repository) exits non-zero: the release jobs never read an error as "no tag". Needs gh and
# GH_TOKEN. Used by facthory-release.yml.
set -euo pipefail
tag=$1
if ! out=$(gh api --paginate "repos/${GITHUB_REPOSITORY}/git/matching-refs/tags/${tag}" \
  --jq ".[] | select(.ref == \"refs/tags/${tag}\") | .object.type + \" \" + .object.sha"); then
  echo "::error::Could not look up tag ${tag}." >&2
  exit 1
fi
[ -n "$out" ] || exit 0
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

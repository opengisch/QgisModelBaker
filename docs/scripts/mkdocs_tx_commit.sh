#!/usr/bin/env bash

set -e

pre-commit install
pre-commit run --files mkdocs.yml || true

if [[ $(git diff --exit-code mkdocs.yml) ]]; then
  git config --global user.email "github-actions[bot]@users.noreply.github.com"
  git config --global user.name "github-actions[bot]"

  echo "detected changes in mkdocs.yml"
  if [[ ${GITHUB_EVENT_NAME} == "pull_request" ]]; then
    # on PR push to the same branch
    gh pr checkout $(echo "${GITHUB_REF_NAME}" | cut -d/ -f1)
    git add mkdocs.yml
    git commit -m "Update mkdocs.yml translation" --no-verify
    git push
  else
    # on push/workflow_dispatch create a pull request
    git checkout ${GITHUB_REF_NAME}
    BRANCH="update-mkdocs-tx-$RANDOM"
    git checkout -b ${BRANCH}
    git add mkdocs.yml
    git commit -m "Update mkdocs.yml translation" --no-verify
    git push -u origin $BRANCH
    gh pr create -B ${GITHUB_REF_NAME} -H ${BRANCH} --title 'Update mkdocs translations' --body 'run from mkdocs_tx'
  fi
else
  echo "no change mkdocs.yml"
fi

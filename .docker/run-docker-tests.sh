#!/usr/bin/env bash
set -e
pushd /usr/src
xvfb-run nose2-3
popd

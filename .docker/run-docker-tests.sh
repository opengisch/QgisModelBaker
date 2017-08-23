#!/usr/bin/env bash
pushd /usr/src
xvfb-run nose2-3
popd

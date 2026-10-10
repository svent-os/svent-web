#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$here/bin"
export GOBIN="$here/bin"
export GOTOOLCHAIN=auto
go install -p "${SVENT_BUILD_JOBS:-2}" -trimpath -ldflags "-s -w" github.com/hakluke/hakrawler@v0.0.0-20260805040537-52a16fe61bd1

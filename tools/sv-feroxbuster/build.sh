#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_directory=$(mktemp -d "$here/.build.XXXXXX")
trap 'rm -rf "$build_directory"' EXIT HUP INT TERM
mkdir -p "$here/bin"
cargo install feroxbuster --version 2.13.1 --locked --jobs "${SVENT_BUILD_JOBS:-2}" --root "$build_directory"
install -m 0755 "$build_directory/bin/feroxbuster" "$here/bin/feroxbuster"

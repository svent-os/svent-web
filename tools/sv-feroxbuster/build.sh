#!/bin/sh
set -eu
here=$(cd "$(dirname "$0")" && pwd)
rm -rf "$here/bin"; mkdir -p "$here/bin"
cargo install feroxbuster --root "$here/.c" --locked && cp "$here/.c/bin/feroxbuster" "$here/bin/" && rm -rf "$here/.c"

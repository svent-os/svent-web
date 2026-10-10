#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_directory=$(mktemp -d "$here/.build.XXXXXX")
trap 'rm -rf "$build_directory"' EXIT HUP INT TERM
mkdir -p "$here/bin" "$build_directory/source"
curl -fL --retry 3 --connect-timeout 30 'https://static.crates.io/crates/feroxbuster/feroxbuster-2.13.1.crate' -o "$build_directory/source.crate"
printf '%s  %s\n' 'b9bdf7d03b5412cb441c0825cb229fa98b6b45f67885055bfaa1ac5559ea6953' "$build_directory/source.crate" | sha256sum -c -
tar -xzf "$build_directory/source.crate" -C "$build_directory/source" --strip-components=1
python3 - "$build_directory/source/src/scanner/requester.rs" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text()
for divisor in (12, 2):
    expression = f"guard.num_documents().is_multiple_of({divisor})"
    if text.count(expression) != 1:
        raise SystemExit("Unexpected Feroxbuster source; compatibility patch aborted.")
    text = text.replace(expression, f"(guard.num_documents() % {divisor} == 0)")
path.write_text(text)
PY
cargo install --path "$build_directory/source" --locked --jobs "${SVENT_BUILD_JOBS:-2}" --root "$build_directory/install"
install -m 0755 "$build_directory/install/bin/feroxbuster" "$here/bin/feroxbuster"

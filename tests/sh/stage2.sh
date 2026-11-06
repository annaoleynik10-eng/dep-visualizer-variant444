#!/bin/sh
# Этап 2: прямые зависимости заданной версии пакета из crates.io.
cd "$(dirname "$0")/../.." || exit 1
show() {
    echo "=== $1"
    ./run.sh "$1"
    echo "(код выхода $?)"
    echo
}
show configs/serde_json.ini
show configs/regex.ini
show configs/rand.ini
show tests/configs/unknown_crate.ini
show tests/configs/unknown_version.ini
show tests/configs/bad_host.ini

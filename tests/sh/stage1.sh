#!/bin/sh
# Этап 1: вывод параметров и обработка ошибок для всех параметров.
cd "$(dirname "$0")/../.." || exit 1
show() {
    echo "=== $1"
    ./run.sh "$1"
    echo "(код выхода $?)"
    echo
}
show configs/serde_json.ini
show configs/test_simple.ini
show tests/configs/nope.ini
for f in tests/configs/*.ini; do
    show "$f"
done

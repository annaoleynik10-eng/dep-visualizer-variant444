#!/bin/sh
# Этап 3: граф зависимостей (BFS), глубина, циклы, тестовый режим.
cd "$(dirname "$0")/../.." || exit 1
show() {
    echo "=== $1"
    ./run.sh "$1"
    echo "(код выхода $?)"
    echo
}
for f in test_simple test_chain_all test_chain_2 test_cycle test_self \
         test_complex test_complex_from_parse; do
    show "configs/$f.ini"
done
show tests/configs/unknown_root.ini
show tests/configs/bad_repo_format.ini
show tests/configs/bad_repo_name.ini
show configs/serde_json.ini

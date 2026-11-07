#!/bin/sh
# Этап 5: текст Mermaid и изображение графа для трёх пакетов crates.io
# и для тестового репозитория. Картинки открываются в браузере,
# файлы сохраняются в папку out/.
cd "$(dirname "$0")/../.." || exit 1
show() {
    echo "=== $1"
    ./run.sh "$1"
    echo "(код выхода $?)"
    echo
}
for f in serde_json thiserror regex test_complex test_chain_2; do
    show "configs/mermaid_$f.ini"
done

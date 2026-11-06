#!/bin/sh
# Этап 4: обратные зависимости (кто зависит от пакета) в тестовом режиме.
cd "$(dirname "$0")/../.." || exit 1
show() {
    echo "=== $1"
    ./run.sh "$1"
    echo "(код выхода $?)"
    echo
}
for f in reverse_simple_d reverse_simple_a reverse_chain_2 reverse_cycle \
         reverse_complex reverse_complex_time; do
    show "configs/$f.ini"
done
show tests/configs/bad_mode.ini
show tests/configs/reverse_real.ini

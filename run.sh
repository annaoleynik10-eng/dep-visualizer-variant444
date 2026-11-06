#!/bin/sh
# Запуск: ./run.sh [путь к config.ini]
DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHONPATH="$DIR/src" exec python3 -m depviz "$@"

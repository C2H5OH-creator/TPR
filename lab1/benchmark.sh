#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CPP_SOURCE_FILE="$SCRIPT_DIR/lab1.cpp"
PY_SOURCE_FILE="$SCRIPT_DIR/lab1.py"
CPP_BINARY_FILE="${TMPDIR:-/tmp}/lab1_benchmark"

compile() {
    g++ -std=c++20 "$CPP_SOURCE_FILE" -o "$CPP_BINARY_FILE"
}

measure() {
    local command="$1"
    local mode="$2"
    local label="$3"
    local elapsed

    elapsed=$(TIMEFORMAT="%R"; { time $command "$mode" >/dev/null; } 2>&1)
    printf "%-18s %s sec\n" "$label" "$elapsed"
}

compile

echo "C++ binary: $CPP_BINARY_FILE"
measure "$CPP_BINARY_FILE" --memo "C++ with memo"
measure "$CPP_BINARY_FILE" --no-memo "C++ without memo"

echo
echo "Python file: $PY_SOURCE_FILE"
measure "python3 $PY_SOURCE_FILE" --memo "Python with memo"
measure "python3 $PY_SOURCE_FILE" --no-memo "Python without memo"

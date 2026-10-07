#!/usr/bin/env bash
# 从上游仓库构建 Meow 解释器，并复制为当前目录下的 meow.jar。
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"
echo "cloning Glavo/MeowLang ..."
git clone --depth 1 https://github.com/Glavo/MeowLang "$TMP/MeowLang"
cd "$TMP/MeowLang"
chmod +x gradlew
./gradlew meow --console=plain
cp meow.jar "$DIR/meow.jar"
echo "built $DIR/meow.jar"

#!/usr/bin/env bash
set -euo pipefail

APP_NAME="FiscalPDF"
ENTRYPOINT="src/main.py"
DIST_DIR="dist"
BUILD_DIR="build"

echo "==> Cleaning old builds"
rm -rf "$DIST_DIR" "$BUILD_DIR" "$APP_NAME.spec"

echo "==> Building $APP_NAME (Linux)"
pyinstaller \
  --clean \
  --onefile \
  --noconsole \
  --name "$APP_NAME" \
  "$ENTRYPOINT"

echo "==> Build complete"
echo "Binary: $DIST_DIR/$APP_NAME"

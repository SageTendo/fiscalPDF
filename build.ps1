$ErrorActionPreference = "Stop"

$APP_NAME = "FiscalPDF"
$ENTRYPOINT = "src/main.py"
$DIST_DIR = "dist"
$BUILD_DIR = "build"

Write-Host "==> Cleaning old builds"
Remove-Item -Recurse -Force -ErrorAction Ignore $DIST_DIR, $BUILD_DIR, "$APP_NAME.spec"

Write-Host "==> Building $APP_NAME (Windows)"
pyinstaller `
  --clean `
  --onefile `
  --noconsole `
  --name $APP_NAME `
  $ENTRYPOINT

Write-Host "==> Build complete"
Write-Host "Binary: $DIST_DIR\$APP_NAME.exe"

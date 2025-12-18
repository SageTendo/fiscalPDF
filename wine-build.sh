wine pipenv run \
  pyinstaller \
  --clean \
  --onefile \
  --noconsole \
  --name FiscalPDF \
  -i assets/icon.ico \
  src/desktop/app.py
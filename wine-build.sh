wine pipenv run \
  pyinstaller \
  --clean \
  --onefile \
  --noconsole \
  --name FiscalPDF \
  src/main.py
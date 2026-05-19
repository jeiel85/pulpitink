$ErrorActionPreference = "Stop"

python -m pip install -r requirements-dev.txt
python -m build

Write-Host "TODO: Add PyInstaller build command"

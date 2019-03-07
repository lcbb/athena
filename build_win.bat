pyinstaller .\src\athena.py --add-data "ui;ui" --add-data "tools;tools" --add-data "sample_inputs;sample_inputs" --version-file version_info.txt %*

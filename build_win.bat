pyinstaller .\src\athena.py --add-data "ui;ui" --add-data "tools;tools" --add-data "sample_inputs;sample_inputs" ^
                            --add-binary "%VIRTUAL_ENV%/Lib/site-packages/PySide2/plugins/geometryloaders;qt5_plugins/geometryloaders" ^
                            --version-file version_info.txt %*

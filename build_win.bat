python .\build_preflight.py
pyinstaller .\src\main.py --add-data "ui;ui" --add-data "tools;tools" --add-data "sample_inputs;sample_inputs" ^
                          --add-data "src/qml;qml" --add-data "src/shaders;shaders" ^
                          --add-data "athena_version.py;version.py" ^
                          --add-binary "%VIRTUAL_ENV%/Lib/site-packages/PySide2/plugins/geometryloaders;qt5_plugins/geometryloaders" ^
                          --version-file version_info.txt --name Athena --icon icon\athena.ico %*

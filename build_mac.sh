#! /bin/sh
pyinstaller ./src/main.py --add-data "ui:ui" --add-data "tools:tools" --add-data "sample_inputs:sample_inputs" \
                          --add-data "src/qml:qml" --add-data "src/shaders:shaders" \
                          --add-binary "${VIRTUAL_ENV}/lib/python3.7/site-packages/PySide2/Qt/plugins/geometryloaders:qt5_plugins/geometryloaders" \
                          --name Athena $*

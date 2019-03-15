#! /bin/sh
pyinstaller ./src/athena.py --add-data "ui:ui" --add-data "tools:tools" --add-data "sample_inputs:sample_inputs" \
                            --add-binary "${VIRTUAL_ENV}/lib/python3.7/site-packages/PySide2/Qt/plugins/geometryloaders:qt5_plugins/geometryloaders" $*

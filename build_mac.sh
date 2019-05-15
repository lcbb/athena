#! /bin/sh
python ./build_preflight.py
pyinstaller ./src/main.py --add-data "ui:ui" --add-data "tools:tools" --add-data "sample_inputs:sample_inputs" \
                          --add-data "src/qml:qml" --add-data "src/shaders:shaders" \
                          --add-data "athena_version.py:." \
                          --add-binary "${VIRTUAL_ENV}/lib/python3.7/site-packages/PySide2/Qt/plugins/geometryloaders:qt5_plugins/geometryloaders" \
                          --osx-bundle-identifier="edu.mit.lcbb.athena" \
                          --name Athena --icon "icon/athena.icns" --windowed $*
plutil -insert NSHighResolutionCapable -bool true dist/Athena.app/Contents/Info.plist
VERSION=`cut -f 2 -d \" athena_version.py`
plutil -replace CFBundleShortVersionString -string `cut -f 2 -d \" athena_version.py` dist/Athena.app/Contents/Info.plist

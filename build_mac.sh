#! /bin/sh
pyinstaller ./src/athena.py --add-data "ui:ui" --add-data "tools:tools" $*

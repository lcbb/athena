#!/bin/sh
set -e

python build_preflight.py

VERSION=`python athena_version.py`

echo "Deploying as version" $VERSION

./build_mac.sh --clean --noconfirm
./sign_mac.sh "LCBB"

rm -rf Athena
mkdir Athena
cp -a dist/Athena.app Athena
cp README.txt Athena
cp LICENSE Athena

ZIPFILE=dist/athena_mac_${VERSION}.zip
echo "Creating ${ZIPFILE}"
zip -y -q -r ${ZIPFILE} Athena


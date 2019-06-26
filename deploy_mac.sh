#!/bin/sh
set -e

python build_preflight.py

VERSION=`python athena_version.py`

echo "Deploying as version" $VERSION

./build_mac.sh --clean --noconfirm
./sign_mac.sh "LCBB"

ZIPFILE=athena_mac_${VERSION}.zip
echo "Creating dist/${ZIPFILE}"
(cd dist; zip -q -r ${ZIPFILE} Athena.app)


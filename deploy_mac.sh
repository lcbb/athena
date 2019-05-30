#!/bin/sh
set -e

if [ -z "$1" ]
  then
    echo "You must supply a version string"
    exit 1
fi

VERSION=${1}

echo "Deploying as version" $VERSION

./build_mac.sh --clean

(cd dist; zip -r athena_mac_${VERSION}.zip Athena.app)


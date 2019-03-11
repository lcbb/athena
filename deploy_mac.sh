#!/bin/sh
set -e

if [ -z "$1" ]
  then
    echo "You must supply a version string"
    exit 1
fi

VERSION=${1}

echo "Deploying as version" $VERSION

./build_mac.sh --clean --onefile

zip -j dist/athena_mac_${VERSION}.zip dist/athena


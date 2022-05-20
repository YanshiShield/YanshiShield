#!/usr/bin/env bash

set -e

CUR_DIR=$(cd $(dirname "$0");pwd)
PROJECT_DIR=$(dirname $(dirname $CUR_DIR))

source $PROJECT_DIR/deploy/scripts/const.properties
cd ${PROJECT_DIR}

# install cli
python3 -m pip install $cli_whl \
                         --disable-pip-version-check --force-reinstall
echo "Install NeurSafe FL Command line interface successfully."

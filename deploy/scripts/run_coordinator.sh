#!/usr/bin/env bash

CUR_DIR=$(cd $(dirname "$0");pwd)

PROJECT_DIR=$(dirname $(dirname $CUR_DIR))

python3 -m neursafe_fl.python.coordinator.app --config_file $1

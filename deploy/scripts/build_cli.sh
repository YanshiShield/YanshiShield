#!/usr/bin/env bash

set -e

CUR_DIR=$(cd $(dirname "$0");pwd)
PROJECT_DIR=$(dirname $(dirname $CUR_DIR))

source $PROJECT_DIR/deploy/scripts/const.properties
cd ${PROJECT_DIR}

# protoc
bash $PROJECT_DIR/deploy/scripts/build_proto.sh
echo "Build proto successfully."

# build cli
bazel build $cli_bazel_obj
echo "Build NeurSafe FL Command line interface successfully."

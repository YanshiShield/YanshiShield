#!/usr/bin/env bash

GETOPT_ARGS=`getopt -o r: -al runtime: -- "$@"`
eval set -- "$GETOPT_ARGS"

while [ -n "$1" ]
do
        case "$1" in
                -r|--runtime) opt_runtime=$2; shift 2;;
                --) break ;;
                *) echo $1,$2; break ;;
        esac
done

set -e

CUR_DIR=$(cd $(dirname "$0");pwd)
PROJECT_DIR=$(dirname $(dirname $CUR_DIR))

source $PROJECT_DIR/deploy/scripts/const.properties
cd ${PROJECT_DIR}

if [ "$opt_runtime" = "tf" ]; then
    echo "Build Tensorflow NeurSafe FL SDK."
    sdk_bazel_obj=$sdk_tf_bazel_obj
elif [ "$opt_runtime" = "torch" ]; then
    echo "Build Pytorch NeurSafe FL SDK."
    sdk_bazel_obj=$sdk_torch_bazel_obj
else
    echo "Build NeurSafe FL SDK."
    sdk_bazel_obj=$sdk_bazel_obj
fi

# protoc
bash $PROJECT_DIR/deploy/scripts/build_proto.sh
echo "Build proto successfully."

# build SDK wheel
bazel build $sdk_bazel_obj
apt-get clean
echo "Build NeurSafe FL SDK successfully."

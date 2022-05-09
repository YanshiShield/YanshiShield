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
    echo "Build Tensorflow NeurSafe FL Client."
    client_bazel_obj=$client_tf_bazel_obj
elif [ "$opt_runtime" = "torch" ]; then
    echo "Build Pytorch NeurSafe FL Client."
    client_bazel_obj=$client_torch_bazel_obj
else
    echo "Build NeurSafe FL Client."
    client_bazel_obj=$client_bazel_obj
fi

# protoc
bash $PROJECT_DIR/deploy/scripts/build_proto.sh
echo "Build proto successfully."

# build client wheel
bazel build $client_bazel_obj
echo "Build NeurSafe FL Client successfully."

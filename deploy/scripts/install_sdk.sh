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
    echo "Install Tensorflow NeurSafe FL SDK."
    sdk_whl=$sdk_tf_whl
elif [ "$opt_runtime" = "torch" ]; then
    echo "Install Pytorch NeurSafe FL SDK."
    sdk_whl=$sdk_torch_whl
else
    echo "Install NeurSafe FL SDK."
    sdk_whl=$sdk_whl
fi

# install SDK
python3 -m pip install $sdk_whl \
                         --disable-pip-version-check --force-reinstall
echo "Install NeurSafe SDK successfully."

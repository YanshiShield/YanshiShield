#!/bin/bash

GETOPT_ARGS=`getopt -o m:http:https:no: -al mode:,http_proxy:,https_proxy:,no_proxy: -- "$@"`
eval set -- "$GETOPT_ARGS"

while [ -n "$1" ]
do
        case "$1" in
                -m|--mode) opt_mode=$2; shift 2;;
                -http|--http_proxy) opt_http_proxy=$2; shift 2;;
                -https|--https_proxy) opt_https_proxy=$2; shift 2;;
                -no|--no_proxy) opt_no_proxy=$2; shift 2;;
                --) break ;;
                *) echo $1,$2; break ;;
        esac
done

set -e

PROJECT_DIR=$(dirname $(dirname $(cd "$(dirname "$0")";pwd)))
cd $PROJECT_DIR


function build_images() {
    dockerfile=$1
    image=$2

    alias docker="/usr/bin/docker"
    echo "------------Build $image----------------"

    docker build --build-arg https_proxy=$opt_https_proxy \
    --build-arg http_proxy=$opt_http_proxy \
    --build-arg no_proxy=no_proxy \
    -t $image -f $dockerfile .

    echo "--------Build $image Successfully-------"
}

echo "Build mode: $opt_mode"
# String schema: {Dockerfile path},,{image}
if [ "$opt_mode" = "minimal" ]; then
    echo "Build NeurSafe FL minimal images."
    image_cfgs=(
      deploy/docker-images/dockerfiles/base.Dockerfile,,nsfl-base:latest
      deploy/docker-images/dockerfiles/client-cpu.Dockerfile,,nsfl-client-cpu:latest
      deploy/docker-images/dockerfiles/coordinator.Dockerfile,,nsfl-coordinator:latest
      )
else
    echo "Build NeurSafe FL all images."
    image_cfgs=(
      deploy/docker-images/dockerfiles/base.Dockerfile,,nsfl-base:latest
      deploy/docker-images/dockerfiles/cli.Dockerfile,,nsfl-cli:latest
      deploy/docker-images/dockerfiles/client-cpu.Dockerfile,,nsfl-client-cpu:latest
      deploy/docker-images/dockerfiles/coordinator.Dockerfile,,nsfl-coordinator:latest
      deploy/docker-images/dockerfiles/job_scheduler.Dockerfile,,nsfl-job-scheduler:latest
      deploy/docker-images/dockerfiles/selector.Dockerfile,,nsfl-selector:latest
      deploy/docker-images/dockerfiles/proxy.Dockerfile,,nsfl-proxy:latest
      deploy/docker-images/dockerfiles/model_manager.Dockerfile,,nsfl-model-manager:latest
      )
fi


for image_cfg in ${image_cfgs[@]}; do
    dockerfile=`echo $image_cfg | awk -F",," '{printf $1}'`
    image=`echo $image_cfg | awk -F",," '{printf $2}'`

    build_images $dockerfile $image
done

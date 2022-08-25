#!/bin/bash

GETOPT_ARGS=`getopt -o r:t:http:https:no: -al registry:,tag:,http_proxy:,https_proxy:,no_proxy: -- "$@"`
eval set -- "$GETOPT_ARGS"

while [ -n "$1" ]
do
        case "$1" in
                -r|--registry) opt_registry=$2; shift 2;;
                -t|--tag) opt_tag=$2; shift 2;;
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


if [ "$opt_tag" = "" ]; then
    opt_tag="latest"
fi


function build_and_push_images() {
    dockerfile=$1
    image=$2
    registry=$3

    if [ "$registry" != "" ]; then
        image=$registry"/"$image;
    fi

    echo "------------Build $image----------------"

    docker build --build-arg https_proxy=$opt_https_proxy \
    --build-arg http_proxy=$opt_http_proxy \
    --build-arg no_proxy=no_proxy \
    -t $image -f $dockerfile .

     if [ "$registry" != "" ]; then
         echo "------------Push $image----------------"
         docker push $image
     fi

    echo "--------Build or push $image Successfully-------"
}


echo "Build NeurSafe FL all images."
# String schema: {Dockerfile path},,{image}},,{docker registry}
image_cfgs=(
  deploy/docker-images/dockerfiles/base.Dockerfile,,nsfl-base:latest
  deploy/docker-images/dockerfiles/cli.Dockerfile,,nsfl-cli:${opt_tag},,$opt_registry
  deploy/docker-images/dockerfiles/client-cpu.Dockerfile,,nsfl-client-cpu:${opt_tag},,$opt_registry
  deploy/docker-images/dockerfiles/coordinator.Dockerfile,,nsfl-coordinator:${opt_tag},,$opt_registry
  deploy/docker-images/dockerfiles/job_scheduler.Dockerfile,,nsfl-job-scheduler:${opt_tag},,$opt_registry
  deploy/docker-images/dockerfiles/selector.Dockerfile,,nsfl-selector:${opt_tag},,$opt_registry
  deploy/docker-images/dockerfiles/proxy.Dockerfile,,nsfl-proxy:${opt_tag},,$opt_registry
  deploy/docker-images/dockerfiles/model_manager.Dockerfile,,nsfl-model-manager:${opt_tag},,$opt_registry
  deploy/docker-images/dockerfiles/data_server.Dockerfile,,nsfl-data-server:${opt_tag},,$opt_registry
  )


for image_cfg in ${image_cfgs[@]}; do
    dockerfile=`echo $image_cfg | awk -F",," '{printf $1}'`
    image=`echo $image_cfg | awk -F",," '{printf $2}'`
    registry=`echo $image_cfg | awk -F",," '{printf $3}'`

    build_and_push_images $dockerfile $image $registry
done

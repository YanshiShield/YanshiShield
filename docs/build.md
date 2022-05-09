# Build

This  tutorial gives the building guidance of all Neursafe FL components, Please select the correct components to build according to the deployment scenario.

All building work needs to be done on the Linux system, and all the commands in this tutorial have been verified on the Ubuntu system.



## Environmental Preparation

### 1. Install Python 3 development environment

 ```
sudo apt update
sudo apt install python3-dev python3-pip
 ```

Note: Python 3.7 is recommended



### 2. Install the build tool Bazel

Neursafe FL uses Bazel as a build tool, please refer to the [official guide document](https://docs.bazel.build/versions/main/install.html) for installation.



### 3. Install docker

Building container images requires a Docker runtime environment, please refer to the [official guide document](https://docs.docker.com/get-docker/)) for installation.



### 4. Clone Neursafe FL code

```shell
git clone https://github.com/neursafe/federated-learning.git
cd federated-learning
```



## Build packages

### 1. Create a Python 3 virtual environment

It is recommended to build and run Neursafe FL in a virtual environment.

```sh
python3 -m venv "venv"
source "venv/bin/activate"
pip install --upgrade pip
```

Note: To exit the virtual environment, run deactivate



### 2. Build Coordinator

```shell
./deploy/scripts/build_coordinator.sh
```



### 3. Build Client

The client package can be build according to the underlying machine learning framework. By default, both Tensorflow and Pytoch support:

```shell
# for Tensorflow and Pytorch
./deploy/scripts/build_client.sh

# for Tensorflow only
./deploy/scripts/build_client.sh --runtime=tf

# for Pytorch only
./deploy/scripts/build_client.sh --runtime=torch
```



### 4. Build Development SDK

The SDK can be build according to the underlying machine learning framework. By default, both Tensorflow and Pytoch support:

```shell
# for Tensorflow and Pytorch
./deploy/scripts/build_sdk.sh

# for Tensorflow only
./deploy/scripts/build_sdk.sh --runtime=tf

# for Pytorch only
./deploy/scripts/build_sdk.sh --runtime=torch
```



### 5. Build NSFL-Ctl

```shell
./deploy/scripts/build_cli.sh
```



## Build container image

Build the Neursafe FL component container images with the following commands:

### 1. Build base image

This container image is the base image for all Neursafe FL components:

```shell
docker build -t nsfl-base:latest -f ./deploy/docker-images/dockerfiles/base.Dockerfile .
```

Note: In all images building, if your environment needs to access the Internet through a proxy, please set the correct proxy configuration as follows:

```
docker build --build-arg https_proxy=proxyhost:port \
--build-arg http_proxy=proxyhost:port \
--build-arg no_proxy="localhost,10.0.0.1/8" \
-t nsfl-base:latest -f ./deploy/docker-images/dockerfiles/base.Dockerfile .
```



### 2. Build Coordinator image

```shell
docker build -t nsfl-coordinator:latest -f ./deploy/docker-images/dockerfiles/coordinator.Dockerfile .
```

Note: The tag of the component image can be customized.



### 3. Build Job Scheduler image

```shell 
docker build -t nsfl-job-scheduler:latest -f ./deploy/docker-images/dockerfiles/job_scheduler.Dockerfile .
```



### 4. Build Client image

```shell
docker build -t nsfl-client-cpu:latest -f ./deploy/docker-images/dockerfiles/client-cpu.Dockerfile .
```



### 5. Build Selector image

```shell
docker build -t nsfl-selector:latest -f ./deploy/docker-images/dockerfiles/selector.Dockerfile .
```



### 6. Build Model Manager image

```shell
docker build -t nsfl-model-manager:latest -f ./deploy/docker-images/dockerfiles/model_manager.Dockerfile .
```



### 7. Build Proxy image

```shell
docker build -t nsfl-proxy:latest -f ./deploy/docker-images/dockerfiles/proxy.Dockerfile .
```



### 8. Build NSFL-Ctl image

```shell
docker build -t nsfl-ctl:latest -f ./deploy/docker-images/dockerfiles/cli.Dockerfile .
```



After building,  please refer to the installation guide to complete the [installation and deployment](install.md) of Neursafe FL.


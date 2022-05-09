# 编译

本文给出所有Neursafe FL组件的编译，请根据部署场景，选择对应的组件进行编译。

所有的编译工作需在Linux系统上完成，文中所有命令均在Ubuntu系统验证通过。



## 环境准备

### 1. 安装Python 3 开发环境

 ```
sudo apt update
sudo apt install python3-dev python3-pip
 ```

注意：推荐使用Python3.7



### 2. 安装编译软件Bazel

Neursafe FL使用Bazel作为编译工具，请参考[官方指导文档](https://docs.bazel.build/versions/main/install.html)进行安装



### 3. 安装docker

编译容器镜像需要Docker运行环境，请参考[官方指导文档](https://docs.docker.com/get-docker/)安装



### 4. 克隆Neursafe FL代码库

```shell
git clone https://github.com/neursafe/federated-learning.git
cd federated-learning
```



## 编译软件包

### 1. 创建Python 3虚拟环境

建议在虚拟环境下编译、运行Neursafe FL

```sh
python3 -m venv "venv"
source "venv/bin/activate"
pip install --upgrade pip
```

注意：要退出虚拟环境，请运行deactivate



### 2. 编译Coordinator

```shell
./deploy/scripts/build_coordinator.sh
```



### 3. 编译Client

可以根据底层运行的机器学习框架进行client的编译，默认Tensorflow和Pytoch均支持：

```shell
# for Tensorflow and Pytorch
./deploy/scripts/build_client.sh

# for Tensorflow only
./deploy/scripts/build_client.sh --runtime=tf

# for Pytorch only
./deploy/scripts/build_client.sh --runtime=torch
```



### 4. 编译联邦开发SDK

可以根据底层运行的机器学习框架进行SDK的编译，默认Tensorflow和Pytoch均支持：

```shell
# for Tensorflow and Pytorch
./deploy/scripts/build_sdk.sh

# for Tensorflow only
./deploy/scripts/build_sdk.sh --runtime=tf

# for Pytorch only
./deploy/scripts/build_sdk.sh --runtime=torch
```



### 5. 编译NSFL-Ctl

```shell
./deploy/scripts/build_cli.sh
```



## 编译容器镜像

通过以下命令完成Neursafe FL各组件容器镜像的编译：

### 1. 编译base镜像

该容器镜像是Neursafe FL所有组件的基础镜像：

```shell
docker build -t nsfl-base:latest -f ./deploy/docker-images/dockerfiles/base.Dockerfile .
```

注意：在所有的镜像编译中，如果你的环境需要通过代理访问互联网，请设置正确的代理配置，如下：

```
docker build --build-arg https_proxy=proxyhost:port \
--build-arg http_proxy=proxyhost:port \
--build-arg no_proxy="localhost,10.0.0.1/8" \
-t nsfl-base:latest -f ./deploy/docker-images/dockerfiles/base.Dockerfile .
```



### 2. 编译Coordinator镜像

```shell
docker build -t nsfl-coordinator:latest -f ./deploy/docker-images/dockerfiles/coordinator.Dockerfile .
```

注意：组件镜像的tag用户可以自定义



### 3. 编译Job Scheduler镜像

```shell 
docker build -t nsfl-job-scheduler:latest -f ./deploy/docker-images/dockerfiles/job_scheduler.Dockerfile .
```



### 4. 编译Client镜像

```shell
docker build -t nsfl-client-cpu:latest -f ./deploy/docker-images/dockerfiles/client-cpu.Dockerfile .
```



### 5. 编译Selector镜像

```shell
docker build -t nsfl-selector:latest -f ./deploy/docker-images/dockerfiles/selector.Dockerfile .
```



### 6. 编译Model Manager镜像

```shell
docker build -t nsfl-model-manager:latest -f ./deploy/docker-images/dockerfiles/model_manager.Dockerfile .
```



### 7. 编译Proxy镜像

```shell
docker build -t nsfl-proxy:latest -f ./deploy/docker-images/dockerfiles/proxy.Dockerfile .
```



### 8. 编译NSFL-Ctl镜像

```shell
docker build -t nsfl-ctl:latest -f ./deploy/docker-images/dockerfiles/cli.Dockerfile .
```



编译完软件包或容器镜像后，请参考[安装指导](install_zh.md)完成Neursafe FL的安装部署


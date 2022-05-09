# 安装部署

根据应用场景的不同，对于仅需快速体验Neursafe FL和联邦学习的场景，我们推荐单机模式安装，这样可以让你快速启动一个联邦训练。对于生产环境，推荐集群模式安装。用于联邦开发的SDK上述两种场景均需安装。



## SDK安装

### 1. 进入Neursafe FL代码库

```shell
cd federated-learning
```



### 2. 安装SDK

根据底层运行的机器学习框架进行SDK的安装，默认Tensorflow和Pytorch均支持：

```shell
# for Tensorflow and Pytorch
./deploy/scripts/install_sdk.sh

# for Tensorflow only
./deploy/scripts/install_sdk.sh --runtime=tf

# for Pytorch only
./deploy/scripts/install_sdk.sh --runtime=torch
```

在Python 3环境下，验证SDK安装是否成功

 ![image-20220426214108287](./images/test_sdk.png)



## 单机模式部署

对于单机模式，可以选择主机进程或容器方式运行。对于容器模式，无需安装，如何在单机模式下运行容器来启动联邦训练过程请参见[快速开始](quick_start_zh.md)。单机模式只需安装coordinator、client组件即可：

### 1. 安装coordinator

```
./deploy/scripts/install_coordinator.sh
```



### 2. 安装client

根据底层运行的机器学习框架进行client的安装，默认Tensorflow和Pytoch均支持：

```shell
# for Tensorflow and Pytorch
./deploy/scripts/install_client.sh

# for Tensorflow only
./deploy/scripts/install_client.sh --runtime=tf

# for Pytorch only
./deploy/scripts/install_client.sh --runtime=torch
```



安装结束可参考[快速入门](quick_start_zh.md)体验联邦学习



## 集群模式部署

即将发布
































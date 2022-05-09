# Installation 

For scenarios where you only need to quickly experience Neursafe FL and federated learning, we recommend installing in standalone mode, which allows you to quickly start a federated training. For production environments, cluster mode installation is recommended. The SDK for federated development needs to be installed in both installation modes.



## SDK Installation

### 1. Enter Neursafe FL code

```shell
cd federated-learning
```



### 2. Install SDK

Install the SDK according to the underlying machine learning framework. By default, both Tensorflow and Pytorch support:

```shell
# for Tensorflow and Pytorch
./deploy/scripts/install_sdk.sh

# for Tensorflow only
./deploy/scripts/install_sdk.sh --runtime=tf

# for Pytorch only
./deploy/scripts/install_sdk.sh --runtime=torch
```

In the Python 3 environment, verify whether the SDK installation is successful.

 ![image-20220426214108287](./images/test_sdk.png)



## Standalone Mode

For standalone mode, you can choose to run as host processes or containers. For container mode, no installation is required. See the [quick start](quick_start.md) document for container mode. In this mode, you only need to install the coordinator and client components:


### 1. Install coordinator

```
./deploy/scripts/install_coordinator.sh
```



### 2. Install client

Install the client according to the underlying machine learning framework. By default, both Tensorflow and Pytoch support:

```shell
# for Tensorflow and Pytorch
./deploy/scripts/install_client.sh

# for Tensorflow only
./deploy/scripts/install_client.sh --runtime=tf

# for Pytorch only
./deploy/scripts/install_client.sh --runtime=torch
```



After the installation, please refer to the [quick start](quick_start.md) to experience federated learning.



## Cluster Mode

Coming soon
































# 偃师盾联邦学习

[![license](https://img.shields.io/github/license/ChengMingZhang-ZTE/federated-learning)](https://opensource.org/licenses/Apache-2.0)[![Neursafe_FL_C](https://github.com/neursafe/federated-learning/actions/workflows/ci.yml/badge.svg)](https://github.com/neursafe/federated-learning/actions/workflows/ci.yml)

[English](README.md)

**偃师盾**为关注AI安全解决方案的开源社区，其中**偃师盾 FL**作为Neursafe的子项目提供联邦学习的解决方案，联邦学习为一种隐私安全的机器学习方法，利用大量驻留在客户设备上的去中心化数据协作完成机器学习模型的训练。Neursafe FL的目标是在隐私安全前提下打造可靠、高效、易用的联邦学习和联邦计算平台。Neursafe FL的特点如下：

* 利用差分隐私、多方安全计算（MPC）以及同态加密等密码学算法来保证隐私安全以及联邦训练过程中中间数据的不可见。
* 提供多种联邦聚合和优化算法来保证不同数据分布情况下模型的收敛性和收敛效率。
* 提供现有机器学习向联邦学习的低成本迁移方案，当前支持Pytorch、Tensorflow/Keras。

## 使用教程

### 编译构建

Neursafe FL支持两种安装模式，单机的最小化安装模式和基于Kubernetes运行的集群模式，具体如下：

- 单机模式：该模式下，仅能进行单一作业的联邦训练，训练过程中，只需作业的Coordinator和Clients参与，适用于快速体验Neursafe FL或者本地验证联邦学习代码的正确性的场景。
- 集群模式：具备完整的Neursafe FL功能和特性，如作业管理和调度能力，客户端的管理和优选等。

单机模式的系统组件支持主机进程方式或容器方式运行，而集群模式所有组件均以容器方式运行，请参见[编译](docs/build_zh.md)文档根据具体安装运行的模式选择对应的编译方式和需要编译的Neursafe FL组件。

### 安装部署

请根据系统的安装运行模式进行Neursafe FL的安装，具体请参见[安装部署](./docs/install_zh.md)文档。

### 快速开始

请参见[快速开始](./docs/quick_start_zh.md)文档了解如何利用Neursafe FL进行联邦训练，在样例中采用单机部署的模式。

## 设计和接口

有关Neursafe FL的设计、算法、接口文档，如下：

### 设计

- [架构](./docs/architecture_zh.md)


### 算法

- [安全算法](./docs/algorithms/secure_algos.md)
- [聚合算法](./docs/algorithms/aggregation_algos.md)



### 接口
- [开发指南](./docs/develop.md)




## 贡献

我们欢迎任何形式的贡献，请参考[CONTRIBUTING](CONTRIBUTING_zh.md)进一步了解。










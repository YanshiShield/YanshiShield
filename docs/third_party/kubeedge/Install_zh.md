## 联邦学习平台部署在kube edge

Kube Edge是一个将边缘设备融入kubernetes集群进行管理的开源项目，请参考[这里](https://github.com/kubeedge/kubeedge)对kube edge进一步了解。

我们的联邦框架支持部署在kube edge之上，以此来支持在边缘设备上实现联邦学习任务，本篇文档将指导你如何将我们的联邦框架组件部署在kube edge上。

------

#### 准备

- 你需要一个已经部署好kubernetes的云端集群
- 你需要准备好你的边缘节点

kube edge与kubernetes的版本兼容性请参考[这里](https://github.com/kubeedge/kubeedge#kubernetes-compatibility)。

云端**kubernetes集群**与**边缘设备(edge)**分别需要预先安装的软件请参考[这里](https://kubeedge.io/en/docs/)。

在下文中，我们将统一把kubernetes集群称为云端，edge节点称为边缘端。



#### 安装

首先请参考[这里](https://kubeedge.io/en/docs/setup/keadm/)详细了解在云端跟边缘端部署kube edge组件的流程，本文档将仅对基本的安装过程进行简要说明。

1. 在云端与边缘端同时安装keadm（镜像版本可根据需求在dockerhub进行检索下载）

   ```
   下载镜像
   docker pull kubeedge/installation-package:v1.11.1
   
   执行命令
   docker run --rm kubeedge/installation-package:v1.11.1 cat /usr/local/bin/keadm > /usr/local/bin/keadm && chmod +x /usr/local/bin/keadm
   ```

2. 在云端部署组件

   ```
   # 如果有需要，请设置网络代理
   # 执行安装
   keadm init --advertise-address="THE-EXPOSED-IP"
   
   # 安装完成后，获取token
   keadm gettoken
   ```

3. 在边缘端部署组件

   ```
   keadm join --cloudcore-ipport=THE-EXPOSED-IP:10000 --token=
   ```

4. 加入完成后，在云端查看确认边缘节点加入成功

   ```
   kubectl get nodes
   ```

   

上述流程完成后，接下来部署我们的联邦学习框架组件。

1. 参照[这里](https://github.com/neursafe/federated-learning/blob/main/docs/install.md)部署联邦学习组件在云端kubernetes集群，并部署在master节点。

   ```
   注意：如在安装kube edge之前，已在kubernetes集群上部署完本联邦学习组件，无需再次部署，仅需要参照下面步骤重新部署task manager组件到边缘节点即可。
   ```

2. 将task manager组件部署到边缘节点上：

   ```
   第一步：编辑task manager的deployment
   kubectl edit deployments nsfl-task-manager
   
   1. 修改其中的nodeSelector字段，将值设置为你的边缘节点名称
   nodeSelector:
       kubernetes.io/hostname: ubuntu
   
   2. 添加hostPort字段，端口号与containerPort保持一致
   ports:
       - containerPort: 30090
         hostPort: 30090
   
   编辑完成后，task manager会自动重新部署到指定的边缘节点上
   
   3. 修改CLUSTER_LABEL_VALUE环境变量值为自定义边缘节点标签值
   	例如：nsfl-edge
   
   第二步：给边缘节点打上标签
   kubectl label node edge-ubuntu kubernetes.io/cluster_id=nsfl-edge
   ```

3. 检查Task manager运行情况

   ```
   在边缘端确定有task manager的容器在运行
   docker ps
   
   在云端查看task manager的状态为running状态，且在运行在边缘节点上
   kubectl get pods -o wide
   ```

   

#### 运行

上述组件均部署完成后，在边缘节点创建联邦作业的架构流程如下图所示：

![1660276795734](.\fl_process.png)

请参考[这里](https://github.com/neursafe/federated-learning/blob/main/docs/cluster_deploy.md#deployment-verification)来创建一个联邦学习作业。



#### 安装过程问题解决

- 如果云端安装失败，重新安装时报错如下：

  ```
  Error: another operation (install/upgrade/rollback) is in progress
  ```

  解决办法：

  ```
  # 此时需要卸载cloud edge，执行如下命令：
  helm history -n kubeedge cloudcore   查看是否存在
  helm uninstall -n kubeedge cloudcore  如果存在，卸载
  
  然后，再次执行安装
  keadm init
  ```

- 边缘端无法加入集群

  ```
  检查云端cloud core组件service端口是否一致
  若不一致，修改edge端配置/etc/kubeedge/config/edgecore.yaml
  修改相应的端口保持一致
  ```

- 加入集群成功，但无法部署pod

  ```
  operation: update, err: use of closed network connection
  ```

  解决办法：

  ```
  重新在云端部署cloudcore组件
  ```

  


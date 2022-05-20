# Cluster Deployment

[中文](cluster_deploy_zh.md)

Deploying Neursafe FL in cluster mode can provide more comprehensive capabilities, such as job scheduling and management, and optimal clients selection. Kubernetes is recommended as the underlying infrastructure to manage Neursafe FL clusters. Neursafe FL is divided into server side and client side, and different deployment modes can be selected, among which:

**Server:** Adopt cluster deployment mode, deploy core components Job Manager, Model Manger, Client Selector, Proxy;

**Client: **According to the specific scenario, choose standalone mode deployment or cluster mode deployment. For example, in the Cross silo scenario, multiple organizations or institutions need to break the data barriers for federated training. It is recommended that the client side also choose the cluster mode, so client can easily to manage different federation tasks.

Note： Please refer to the [Neursafe FL framework](architecture.md) for the functions of related core components .



##  Preconditions 

### 1. Install Kubernetes 

On the server side and all clients that choose to deploy in cluster mode, Kubernetes must be successfully installed in the environment. For specific installation, please refer to the [official guide](https://kubernetes.io/docs/setup/). 



### 2. Install distributed file system 

Regardless of the server side or the client side, if it is deployed in a cluster, it is recommended to install a distributed file system system that supports S3 or Posix file interface access, such as Minio, for the installation of Minio, refer to the [official guide](https://github.com/minio/minio).

Note: If the distributed file system requires an account and password to log in, please create a K8S Secret object to store the account and password.



### 3.  Install S3FS 

If Minio is installed, you need to install S3FS to mount the S3-compatible object storage to the local file system of all nodes, so that Kubernetes can directly mount the local file system without feeling the underlying specific distributed file system. S3FS installation reference [official guidance](https://github.com/s3fs-fuse/s3fs-fuse) . 



Create directory on all nodes for Neursafe FL's components to store data, such as configuration files, scripts, data, etc.:

```shell
mkdir -p /mnt/neursafe_fl
```

Note: The created directory needs to be mounted to the distributed file system using S3FS, and all nodes can share the directory.



### 4.  Deploy database 

1. Neursafe FL supports MongoDB and PostgreSQL databases and needs to be deployed in advance. For specific deployment, please refer to [MongoDB Installation Guide](https://www.mongodb.com/docs/manual/installation/), [PostgreSQL Installation Guide](https://www .postgresql.org/docs/)

   Note: Create K8S Secret object to store database account and password

2. For the first installation, you need to initialize the database, create a database to store job, model, and task information. The specific database name and table name are configured according to your specific environment:

   - **postgreSQL**

     ```sql
     CREATE DATABASE neursafe_fl;
     
     \c neursafe_fl;
     
     CREATE TABLE jobs (
         id serial primary key,
         data jsonb
     );
     
     CREATE TABLE models (
         id serial primary key,
         data jsonb
     );
     
     CREATE TABLE tasks (
         id serial primary key,
         data jsonb
     );
     ```

      ![](images/cluster_deploy/init_postgreSQL.png)

   - **MongoDB**

     ```shell
     use neursafe_fl
     
     db.createCollection("jobs")
     
     db.createCollection("models")
     
     db.createCollection("tasks") ![](images/cluster_deploy/init_mongodb.png)
     ```

      ![](images/cluster_deploy/init_mongodb.png)



### 5. Build images

 Execute the following command to build the images of all components of Neursafe FL and push them to the specified docker images repository: 

```shell
./deploy/scripts/build_images.sh --registry registryip:port --tag latest --https_proxy proxyhost:port --http_proxy proxyhost:port --no_proxy "localhost"
```

**Parameter parsing:**

registry: If the docker registry address is set, the builded images will be pushed to the specified docker registry.

tag: The user can specify the tag of the images, the default is latest.

https_proxy, http_proxy, no_proxy: If your environment needs to access the internet through a proxy, please set the correct proxy configuration.



## Server deployment 

The server side adopts the cluster deployment mode by default, and deploys Job Scheduler, Model Manager, Client Selector, Proxy, and API Server on Kubernetes.



### Deploy Job Scheduler

1. Prepare the deployment script job-scheduler.yaml of Job Scheduler. Please refer to [Deployment Configuration Instructions](develop.md) for the environment variables that need to be configured in yaml, and you can refer to the template job-scheduler.yaml in the deploy/kubernetes/yamls/ directory

   Note: Please configure according to your K8S environment

2.  Execute the following command to deploy Job Scheduler:

   ```shell
   kubectl create -f job-scheduler.yaml
   ```

   

3.  To verify whether the deployment is successful, execute the following command to check whether the Pod of the Job Scheduler is in the Runnin state:

   ```shell
    kubectl get pod
   ```

    ![](D:/★近期工作/联邦开源工作/终稿/federated-learning/docs/images/cluster_deploy/job_scheduler_running.png)

   

### Deploy Model Manager

1. Prepare the deployment script model-manager.yaml of Model Manager. Please refer to [Deployment Configuration Instructions](develop.md) for the environment variables that need to be configured in yaml. You can refer to the template model-manager.yaml in the deploy/kubernetes/yamls/ directory

   Note: Please configure according to your K8S environment

2.  Execute the following command to deploy Model Manager:

   ```shell
   kubectl create -f model-manager.yaml
   ```

   

3.  To verify whether the deployment is successful, execute the following command to check whether the Pod of the Model Manager is Running state:

   ```shell
   kubectl get pod
   ```

    ![](D:/★近期工作/联邦开源工作/终稿/federated-learning/docs/images/cluster_deploy/model_manager_running.png)

   

### Deploy Client Selector

1. Prepare the deployment script selector.yaml of the Client Selector. For the environment variables that need to be configured in the yaml, please refer to  [Deployment Configuration Instructions](develop.md). You can refer to the template selector.yaml in the deploy/kubernetes/yamls/ directory.

   Note: Please configure according to your K8S environment. In addition, please refer to  [Deployment Configuration Instructions](develop.md) for the setup parameters of ClientSelector to configure in comnand of yaml  script.

2. Execute the following command to deploy Client Selector:

   ```shell
   kubectl create -f selector.yaml
   ```

   

3. To verify whether the deployment is successful, execute the following command to check whether the Pod of the Client Selector is Running state:

   ```shell
   kubectl get pod
   ```

    ![](D:/★近期工作/联邦开源工作/终稿/federated-learning/docs/images/cluster_deploy/client_selector_running.png)

   

### Deploy Proxy

1. Prepare the deployment script proxy.yaml of Proxy, and the environment variables that need to be configured in yaml, please refer to [Deployment [Deployment Configuration Instructions](develop.md), you can refer to the template proxy.yaml in the deploy/kubernetes/yamls/ directory

   Note: Please configure according to your K8S environment

   

2. Prepare nginx.conf, refer to deploy/configs/proxy/conf/nginx.conf, the default configuration has been put into the proxy image, if you modify the relevant configuration, please mount the new nginx.conf in the above proxy.yaml to the Pod's /nginx/conf/nginx.conf

   

3. Execute the following command to deploy Proxy

   ```shell
   kubectl create -f proxy.yaml
   ```

   

4. To verify whether the deployment is successful, execute the following command to check whether the Pod of the Proxy is Running state

   ```shell
   kubectl get pod
   ```

    ![](D:/★近期工作/联邦开源工作/终稿/federated-learning/docs/images/cluster_deploy/proxy_running.png)



### Deploy API Server

Use K8S Ingress to realize the function of API Server



1. To deploy ingress nginx, please refer to ingress-nginx.yaml in the directory of deploy/kubernetes/yamls/, in fact, the port configuration in the service object refers to your specific environment:

   ```shell
   kubectl create -f ingress-nginx.yaml
   ```

   

2. To configure the routing rules of Job Scheduler, you can refer to the template ingress-job-scheduler.yaml in the deploy/kubernetes/yamls/ directory

   Note: Please configure the serviceName in yaml according to your specific environment

   ```shell
   kubectl create -f ingress-job-scheduler.yaml
   ```

   

3. To configure the routing rules of Model Manager, you can refer to the template ingress-model-manager.yaml in the deploy/kubernetes/yamls/ directory

   Note: Please configure the serviceName in yaml according to your specific environment

   ```shell
   kubectl create -f  ingress-model-manager.yaml
   ```

   

4. To verify whether the deployment is successful, execute the following command to check whether the Pod of the Ingress-Nginx is Running state

   ```shell
   kubectl get pod -n ingress-nginx
   ```

   <img src="D:/★近期工作/联邦开源工作/终稿/federated-learning/docs/images/cluster_deploy/ingress_nginx_running.png" style="zoom:150%;" />



## Task Manager（Client）Deployment

Different clients can choose different deployment modes: standalone mode and cluster mode



### Standalone Mode

1. Prepare the setup configuration setup.json of the Task Manager, refer to the description of the client setup configuration parameters in [Deployment Configuration Instructions](develop.md)

   

2. Run client container

   ```shell
   docker run -v /workspace/neursafe_fl/task_manager/:/workspace/neursafe_fl/task_manager/ --net=host nsfl-client-cpu --config_file /workspace/neursafe_fl/task_manager/setup.json
   ```

   Note: 1. Please use the correct client image name generated by your own building environment; 2. Mount the required data, configuration, directory, etc. into the container



### Cluster Mode

1. Prepare the setup configuration setup.json of the Task Manager, refer to the description of the client setup configuration parameters in [Deployment Configuration Instructions](develop.md)

   

2. Prepare the deployment script task-manager.yaml of Task Manager. Please refer to [Deployment Configuration Instructions](develop.md) for the environment variables that need to be configured in yaml. You can refer to the template task-manager.yaml in the deploy/kubernetes/yamls/ directory

   Note: Please configure according to your K8S environment

   

3. Execute the following command to deploy Task Manager

   ```shell
   kubectl create -f task-manager.yaml
   ```

   

4. To verify whether the deployment is successful, execute the following command to check whether the Pod of the Task Manager is Running state

   ```shell
   kubectl get pod
   ```

    ![](D:/★近期工作/联邦开源工作/终稿/federated-learning/docs/images/cluster_deploy/task_manager_running.png)

   

## Deployment Verification

1. Prepare a training script, evaluation script, initial model, configuration of a federated job tf_mnist_fl according to the configuration instructions of the job in [Deployment Configuration Instructions](develop.md)

    ![](D:/★近期工作/联邦开源工作/终稿/federated-learning/docs/images/cluster_deploy/mnist_dir.png)

   

2. Refer to the instructions for using the command line client in [Deployment Configuration Instructions](develop.md) to create a federated job and execute the following commands

   ```shell
   nsfl-ctl create job -w tf_mnist_fl/ default
   ```

   ![](D:/★近期工作/联邦开源工作/终稿/federated-learning/docs/images/cluster_deploy/create_job.png)

   

3. Query running state of federated job

   ```shell
   nsfl-ctl get job -w tf_mnist_fl/ default
   ```

    ![](D:/★近期工作/联邦开源工作/终稿/federated-learning/docs/images/cluster_deploy/get_job.png)
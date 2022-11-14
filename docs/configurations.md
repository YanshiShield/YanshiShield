
## Component Launch Configuration

Some components of the federated framework need launch configurations. This doc will detail the configuration of each component. There are three types of configuration:
- Command Line: When starting the program, specify some parameters following the command line, usually some simple and basic parameters.
- Config file: When starting the program, specify the corresponding configuration file by '-f', usually is a json format file. Configuration file supports more parameter settings. (Command Line generally is a subset of Config file.)
- ENV: By means of environment variables, usually some external service configuration.


Each component's configuration will be described in detail below.

## Table of Contents

[Component Launch Configuration](#component-launch-configuration)

- [Coordinator](#coordinator)
  - [Command Line](#command-line)
  - [Config File](#config-file)
  - [ENVS](#envs)
- [Client](#client)
  - [Command Line](#command-line-1)
  - [Config file](#config-file-1)
  - [ENVS](#envs-1)
- [Selector](#selector)
  - [Command Line](#command-line-2)
  - [Config file](#config-file-2)
    - [ExtenderConfig](#extenderconfig)
  - [ENVS](#envs-2)
- [Job Scheduler](#job-scheduler)
  - [ENVS](#envs-3)
- [Model Manager](#model-manager)
  - [ENVS](#envs-4)
- [Data Server](#data-server)
  - [ENVS](#envs-5)



## Component Launch Configuration

### Coordinator

The Configuration can be passed in through the command line with args or configuration file. However, the command line only support some basic configurations to startup, if you need a complete configuration, you should use a config file. The detailed description is as follows.

#### Command Line

| args name   | type   | required | description                                                  |
| ----------- | ------ | -------- | ------------------------------------------------------------ |
| job_name    | string | yes      | job name, the federated job name.                            |
| description | string | no       | some detailed information for this job.                      |
| output      | string | no       | job result output directory, such as the checkpoints, final model etc, will be saved in this directory. <br>Default is under current work dir. |
| host        | string | no       | IP address to serve for gRPC service.<br>Default is localhost |
| port        | int    | no       | port to listen on for gRPC API, the range is 1024~65535. <br>Default port is 55051. |
| clients     | string | yes      | Config clients to participate in this job. Using ip:port to represent one client service address, split by ","<br/>For example: 1 client      "127.0.0.1:8888"<br/>                        2 clients    "127.0.0.1:8888, 192.0.0.1:7777" |
| task_entry  | string | yes      | Client task entrypoint, used to specify task name to client. Typically is the script entrypoint name of the training task. |
| model_path  | string | yes      | Local path of model, Which is the initial global model to broadcast to client for training. |
| runtime     | string | yes      | Model runtime used for loading and training model, allowed model runtime: (tensorflow, pytorch). <br/>More runtimes will be supported in future versions. |
| log_level   | string | no       | Log level, support [DEBUG, INFO, WARNING, ERROR].<br>Default is INFO |
| ssl         | string | no       | ssl path, If use gRPCs, you must set the ssl path. the path should have certificate files. [here](https://grpc.io/docs/guides/auth/) is how to create certificate files and using gRPCs. |
| config_file | string | no       | Path to the configuration file. More detailed configuration can be configured in the configuration file, such as hyper parameters, algorithms etc. If used, configured args above will be replaced if the configuration file contains the same args. |



#### Config File

In addition to supporting the above command line parameters, the file also supports following configurations. Config file fomat is `json`.

```
Note: The command line args is a sub-set of config file. If you set same args both in command line and config file, the command line will be ignored.
we highly recommand to use the configuration file.
```

| args name        | type              | required | description                                                  |
| ---------------- | ----------------- | -------- | ------------------------------------------------------------ |
| hyper_parameters | `HyperParameters` | no       | The hyper parameters of federated training. If not configured, will be filled with default training  parameters |
| parameters       | `Parameters`      | no       | The parameters that need to be passed to all training clients, need to be customized by the user |
| datasets         | string            | no       | The dataset to use for the job, when there are multiple datasets, seperated by ',', for example: "dataset1, dataset2" |
| resource         | `Resource`        | no       | The required client resource to running the federated training |
| extender         | `Extenders`       | no       | The extender interface configuration, through this interface, the custom extended interface scripts and functions can be injected into the federation process |
| secure_algorithm | `SecureAlgorithm` | no       | Federated security algorithm configuration. If configured, the training process will protect the intermediate data of the job under the corresponding secure computing method. |
| scripts          | `ScriptConfig`    | no       | The training scripts to broadcast to all the clients. This configuration is suitable for the scene that clients has no scripts in local |
| optimizer        | `Optimizer`       | no       | Optimizer cofiguration, currently for non iid datasets, you can use fedprox, scaffold two optimizers |
| loss             | Loss              | no       | Loss cofiguration, currently   you can use feddc loss for non iid datasets. |



#### ENVS

```
Note: Environment variables are usually configured before startup. Usually, some service addresses, constants, etc. are configured in the environment variables. If a container environment is used, it can be set when the container starts.
```

| ENV                        | Default     | Description                                                  |
| -------------------------- | ----------- | ------------------------------------------------------------ |
| REPORT_PERIOD              | 10          | The time interval for the client to report its own status information， unit is second. Typically, the more stable the client can set the larger value |
| JOB_SCHEDULER_ADDRESS      | None        | If the Job Scheduler component exists, set the service address(ip:port). If you set this address, then federated job process will be reported regularly |
| SELECTOR_ADDRESS           | None        | The selector component address, if set this address, the coordinator will choose clients for federated job from the selector's interface |
| CKPT_ROOT_PATH             | checkpoints | Default directory name to save the checkpoint during the federated training process. |
| DEPLOYMENT_WAY             | cloud       | The deployment method of the coordinator, support cloud or local. If cloud, the should set the COORDINATOR_WORKSPACE_PATH, which is the root work directory of federated job. |
| COORDINATOR_WORKSPACE_PATH | /fl         | The mounted root directory of federated job in the cloud storage. |
| K8S_IMAGE_PULL_SECRETS     | None        | Set imagePullSecrets in k8s pod or deployment to pull image If need |



### Client

The Configuration can be passed in through the command line with args or configuration file. However, the command line only support some basic configurations to startup, if you need a complete configuration, you should use a config file. The detailed description is as follows.

```
Note: we highly recommand to use the configuration file.
```

#### Command Line

| args name         | type   | required | description                                                  |
| ----------------- | ------ | -------- | ------------------------------------------------------------ |
| host              | string | no       | Client listen host, default is '0.0.0.0'                     |
| port              | int    | no       | Client listen port, default is 22000                         |
| server            | string | yes      | The address of server, format is ip:port, where to report the the train or evaluate result.<br>For example: 192.0.0.1:9000 |
| workspace         | string | yes      | Client's workspace path, where used to save some temporary files. These temporary files are generated during the task running, such as checkpoints, task result, etc. |
| platform          | string | no       | Client's platform, support [k8s, linux], default is linux |
| task_config_entry | string | yes      | This is a path to store task_config.json. The task_config.json indicate the path of the entrypoint scripts that the task need to run |
| storage_quota     | int    | no       | The storage quota of client (unit is MB), which limit the size of workspace. When storage_quota is exceeded, the long-standing temporary files in workspace will be deleted |
| log_level         | string | no       | Log level, support [DEBUG, INFO, WARNING, ERROR]<br>default is INFO |
| ssl               | string | no       | ssl path, If use gRPCs, you must set the ssl path. the path should have certificate files. [here](https://grpc.io/docs/guides/auth/) is how to create certificate files and using gRPCs. |
| datasets          | string | yes      | A path to store a JSON file, in which describes the mapping relationship between dataset name and dataset path. This file indicates the dataset supported by the client for federated job |
| config_file       | string | no       | Path to the configuration file. More detailed configuration can be configured in the configuration file. Configured args above will be replaced if the configuration file contains the same args. |



#### Config file

In addition to supporting the above command line parameters, the file also supports following configurations. Config file fomat is `json`.

```
Note: The command line args is a sub-set of config file. If you set same args both in command line and config file, the command line will be ignored.
```

| args name            | type   | required | description                                                  |
| -------------------- | ------ | -------- | ------------------------------------------------------------ |
| client_id            | string | no       | The unique identifier of the client |
| external_address     | string | no       | The IP address and port of the client's external service, Default is host:port |
| registration         | bool   | no       | Whether the client is registered to the selector component. Default is true |
| label                | string | no       | Client's label, which can be used to classify and filter devices |
| runtime              | string | no       | Client supported runtimes, which can be used to classify and filter devices |
| task_saving_strategy | string   | no       | The task storage strategy supports two strategies of mongo/postgreSQL. if not set, The client will not save task history information. If set mongo/postgreSQL, this refers to saving task history information to the mongo/postgreSQL database.  |
| max_task_parallelism | int    | no       | The maximum number of concurrent federated job on the client |
| username             | string | no       | Client's username, used to authentication. Only used when registration is true. |
| password             | string | no       | Client's password, used to authentication. Only used when registration is true. |
| public_key           | string | no       | The path to store the public key,  see [here](https://www.pycrypto.org/) how to generate public keys. |
| private_key          | string | no       | The path to store the private key, see [here](https://www.pycrypto.org/) how to generate private keys. |
| certificate          | string | no       | The path to store the certificate, see [here](https://pypi.org/project/pyOpenSSL/) how to generate and load certificate. |

 

#### ENVS

```
Note: Environment variables are usually configured before startup. If a container environment is used, it can be set when the container starts.
```

| ENV                          | Default | Description                                                  |
| ---------------------------- | ------- | ------------------------------------------------------------ |
| WORKSPACE | /worksapce | The workspace of this component |
| CONTAINER_EXECUTOR_IMAGE     | None    | If the client's task execution environment is kubernetes, then should specify the image address |
| WORKER_PORT                  | 8050    | Service port when the task is executed                       |
| WAIT_WORKER_FINISHED_TIMEOUT | 300     | Maximum time to wait for a task to complete, if not, the task will be stopped forcely |
| WORKER_HTTP_PROXY            | None    | Set up pod environment of http proxy if need                 |
| WORKER_HTTPS_PROXY           | None    | Set up pod environment of https proxy if need                |
| K8S_IMAGE_PULL_SECRETS       | None    | Set imagePullSecrets in k8s pod or deployment to pull image If need |
| DB_TYPE                       | mongo                | The type of database, support ["mongo", "postgreSQL"]        |
| DB_ADDRESS                    | None                 | The service address of database                              |
| DB_USERNAME                   | None                 | The username to login the database                           |
| DB_PASSWORD                   | None                 | The password to login the database                           |
| DB_NAME                       | None                 | The used database name                                       |
| COLLECTION_NAME               | None                 | The used db collection name                                  |
| STORAGE_TYPE                  | posix                | The storage protocol used by the backend storage             |
| S3_ENDPOINT                   | None                 | If protocol type of distributed storage is s3, configure the endpoint of  DFS |
| S3_ACCESS_KEY                 | None                 | If protocol type of distributed storage is s3, configure the access key of DFS |
| S3_SECRET_KEY                 | None                 | If protocol type of distributed storage is s3, configure the secret key of DFS |
| WORKSPACE_BUCKET              | None                 | If protocol type of distributed storage is s3, configure the bucket used |
| WORKSPACE_PVC | None | If protocol type of distributed storage is POSIX, configure the pvc used |
| K8S_ADDRESS                   | None                 | The service address of Kubernetes                            |
| K8S_API_PROTOCOL              | http                 | The protocol used to access the k8s api server               |
| K8S_API_TOKEN                 | None                 | If the K8S api server requires token authentication, a valid token value needs to be configured |
| K8S_IMAGE_PULL_SECRETS        | None                 | If the docker repository requires authentication, you need to configure the corresponding secret |
| GPU_RS_KEY                    | nvidia.com/gpu       | If the cluster has GPU resources, set the resource key value of GPU resources of k8s |
| K8S_NAMESPACE                 | default              | Which namespace of k8s the related components deploy in      |

### Selector

The selector component is mainly used to select the suitable clients for the federated job. The detailed configuration instructions are as follows:

```
Note: The selector component is not mandatory. you can also directly configure the client's service address to join the federated job. However, when you don't know the client, and there are a large number of clients, especially in the cross-device scenarios, such as mobile phone, sensors.
```

#### Command Line

| args name      | type   | required | description                                                  |
| -------------- | ------ | -------- | ------------------------------------------------------------ |
| host           | string | no       | IP address to serve for gRPC API., default is '0.0.0.0'      |
| port           | int    | no       | Port to listen on for gRPC API, the range is 1024~65535. Default port is 50055. |
| log_level      | string | no       | Log level, support [DEBUG, INFO, WARNING, ERROR].<br/>Default is INFO |
| auth_client    | string | no       | Verify the legitimacy of the client. If True, the client should send its certificate or public key. Only the clients pass the authentication can join the federaed job. Default is False. |
| root_cert      | string | no       | The root certificate path, root certificate is used to verify the legitimacy of client, see [here](https://pypi.org/project/pyOpenSSL/) how to generate and load certificate. |
| ssl            | string | no       | ssl path, If use gRPCs, you must set the ssl path. the path should have certificate files. [here](https://grpc.io/docs/guides/auth/) is how to create certificate files and using gRPCs. |
| optimal_select | bool   | no       | Whether the client will be selected by optimal strategy. If set False, the selector will random select client after filter. If set True, you can config the strategy in config file, or using the default strategy. |
| config_file    | string | no       | Path to the configuration file. More detailed configuration can be configured in the configuration file. Configured args above will be replaced if the configuration file contains the same args. |



#### Config file

```
Note: The command line args is a sub-set of config file. If you set same args both in command line and config file, the command line will be ignored.
You can config the strategies and extensions for evaluating and filtering clients.
```

| args name | type | required | description                                                  |
| --------- | ---- | -------- | ------------------------------------------------------------ |
| strategy  | dict | no       | Strategy is used to score the clients, prioritize clients for federated job.<br>Strategy is composed with a few evaluators, with dict format, such as:<br/>        Key: evaluator_name     Value: weight_value<br/>        {<br/>            "resource": 1,<br/>            "data": 1<br/>        }<br/>The Strategy will use every evaluator in the config to score the client, then add up all the scores, which as the final score of client. |
| extenders | dict | no       | Extender is used to extend the process client selection, it will be called after the strategy execution. Support extenders = ["filter", "score"]. For example:<br>{<br/>                "filter": `ExtenderConfig`,<br/>                "score": `ExtenderConfig`<br/> } |

##### ExtenderConfig

| name        | type   | required | description                                    |
| ----------- | ------ | -------- | ---------------------------------------------- |
| mode        | string | yes      | The form of extender, current support ["file"] |
| path        | string | yes      | The absolute path of extension script          |
| method_name | string | yes      | The name of the extension function             |



#### ENVS

| ENV              | Default | Description                                                  |
| ---------------- | ------- | ------------------------------------------------------------ |
| SINGLE_HEART     | 300     | The time interval at which the selector requires the client to report, if the client is a single device |
| CLUSTER_HEART    | 600     | The time interval at which the selector requires the client to report, if the client is a cluster, which means more stable |
| STORAGE_TYPE     | posix   | The storage protocol used by the backend storage             |
| S3_ENDPOINT      | None    | If protocol type of distributed storage is s3, configure the endpoint of  DFS |
| S3_ACCESS_KEY    | None    | If protocol type of distributed storage is s3, configure the access key of DFS |
| S3_SECRET_KEY    | None    | If protocol type of distributed storage is s3, configure the secret key of DFS |
| WORKSPACE_BUCKET | None    | If protocol type of distributed storage is s3, configure the bucket used |



### Job Scheduler

```
Note: Job Scheduler is mainly responsible for scheduling tasks and interacting with multiple modules. There are no startup parameters, mainly some environment variable configurations.
```

#### ENVS

| ENV                           | Default              | Description                                                  |
| ----------------------------- | -------------------- | ------------------------------------------------------------ |
| HTTP_PORT                     | None                 | The service port on which this job scheduler component runs  |
| DB_TYPE                       | mongo                | The type of database, support ["mongo", "postgreSQL"]        |
| DB_ADDRESS                    | None                 | The service address of database                              |
| DB_USERNAME                   | None                 | The username to login the database                           |
| DB_PASSWORD                   | None                 | The password to login the database                           |
| DB_NAME                       | None                 | The used database name                                       |
| COLLECTION_NAME               | None                 | The used db collection name                                  |
| WORKSPACE                     | /worksapce           | The workspace of this component                              |
| TEMP_DIR                      | /coordinator_configs | The relative path of the coordinator configs directory which store dynamically generated coordinator startup configuration files |
| STORAGE_TYPE                  | posix                | The storage protocol used by the backend storage             |
| S3_ENDPOINT                   | None                 | If protocol type of distributed storage is s3, configure the endpoint of  DFS |
| S3_ACCESS_KEY                 | None                 | If protocol type of distributed storage is s3, configure the access key of DFS |
| S3_SECRET_KEY                 | None                 | If protocol type of distributed storage is s3, configure the secret key of DFS |
| WORKSPACE_BUCKET              | None                 | If protocol type of distributed storage is s3, configure the bucket used |
| WORKSPACE_PVC                 | None                 | If protocol type of distributed storage is POSIX, configure the pvc used |
| COORDINATOR_IMAGE             | None                 | The docker image address of Coordinator component            |
| COORDINATOR_WORKSPACE_PATH    | None                 | The workspace of coordinator                                 |
| COORDINATOR_PORT              | 50051                | The service port of coordinator                              |
| CLOUD_OS                      | k8s                  | The system operating environment of each component           |
| DEPLOYMENT_WAY                | cloud                | The deployment method of component, default is in kubernetes |
| K8S_ADDRESS                   | None                 | The service address of Kubernetes                            |
| K8S_API_PROTOCOL              | http                 | The protocol used to access the k8s api server               |
| K8S_API_TOKEN                 | None                 | If the K8S api server requires token authentication, a valid token value needs to be configured |
| K8S_IMAGE_PULL_SECRETS        | None                 | If the docker repository requires authentication, you need to configure the corresponding secret |
| GPU_RS_KEY                    | nvidia.com/gpu       | If the cluster has GPU resources, set the resource key value of GPU resources of k8s |
| K8S_NAMESPACE                 | default              | Which namespace of k8s the related components deploy in      |
| MODEL_MANAGER_ADDRESS         | None                 | The service address of Model Manager component               |
| PROXY_ADDRESS                 | None                 | The service address of Proxy Component                       |
| JOB_SCHEDULER_ADDRESS         | None                 | The service address of Job Scheduler component               |
| SELECTOR_ADDRESS              | None                 | The service address of Selector Component                    |
| REPORT_PERIOD                 | 10                   | The report time interval of coordinator                      |
| COORDINATOR_HEARTBEAT_TIMEOUT | 20                   | The maximum time interval reported by the coordinator, if timeout, the coordinator will be deleted, the jod will set to failed |
| MAX_RETRY_TIMES               | 30                   | Maximum number of attempts to connect                        |
| COORDINATOR_QUERY_INTERVAL    | 1                    | The retry time interval after schedule the coordinator       |



### Model Manager

#### ENVS

| ENV                | Default    | Description                                                  |
| ------------------ | ---------- | ------------------------------------------------------------ |
| PORT               | 50057      | The service port of this component                           |
| LOG_LEVEL          | INFO       | The log level, support [DEBUG, INFO, WARNING, ERROR]         |
| DB_TYPE            | mongo      | The type of database, support ["mongo", "postgreSQL"]        |
| DB_ADDRESS         | None       | The service address of database                              |
| DB_USERNAME        | None       | The username to login the database                           |
| DB_PASSWORD        | None       | The password to login the database                           |
| DB_NAME            | None       | The used database name                                       |
| DB_COLLECTION_NAME | None       | The used db collection name                                  |
| WORKSPACE          | /worksapce | The workspace of this component                              |
| MODELS_DIR         | models     | The relative path where all models are stored in the workspace |
| STORAGE_TYPE       | posix      | The storage protocol used by the backend storage             |
| S3_ENDPOINT        | None       | If protocol type of distributed storage is s3, configure the endpoint of  DFS |
| S3_ACCESS_KEY      | None       | If protocol type of distributed storage is s3, configure the access key of DFS |
| S3_SECRET_KEY      | None       | If protocol type of distributed storage is s3, configure the secret key of DFS |
| WORKSPACE_BUCKET   | None       | If protocol type of distributed storage is s3, configure the bucket used |



### Data Server

#### ENVS

| ENV              | Default    | Description                                                  |
| ---------------- | ---------- | ------------------------------------------------------------ |
| SERVER_ADDRESS   | 0.0.0.0    | The service address of this component                        |
| PORT             | 30088      | The service port of this component                           |
| LOG_LEVEL        | INFO       | The log level, support [DEBUG, INFO, WARNING, ERROR]         |
| WORKSPACE        | /worksapce | The workspace of this component                              |
| STORAGE_TYPE     | posix      | The storage protocol used by the backend storage             |
| ACCESS_USER      | None       | User name for data server authentication                     |
| ACCESS_PASSWORD  | None       | Password for data server authentication                      |
| S3_ENDPOINT      | None       | If protocol type of distributed storage is s3, configure the endpoint of  DFS |
| S3_ACCESS_KEY    | None       | If protocol type of distributed storage is s3, configure the access key of DFS |
| S3_SECRET_KEY    | None       | If protocol type of distributed storage is s3, configure the secret key of DFS |
| WORKSPACE_BUCKET | None       | If protocol type of distributed storage is s3, configure the bucket used |


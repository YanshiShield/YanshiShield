# Compression

## Background

In the whole training process of federated learning, after each round of training, each client needs to upload the delta weights to the Coordinator. The communication overhead will lead to relatively low efficiency of federated training. Therefore, compressing the transmitted data will effectively improve the efficiency of federated training. This paper introduces the theory and usage of the relevant compression algorithms, as well as the relevant experiments to compare and verify the feasibility of the compression algorithms.



## Test environmental preparation

The compression experiments in this directory are based on CIFAR10 dataset and VGG16 model, two federated clients participate in federated training, and the sample data for federated training is split according to the IID method. In order to compare the convergence efficiency, we set the client to perform only one epoch iteration per round.

All experiments are executed in local for algorithm verification. For the generation of configuration scripts related to federated training, please refer to the chapter "Prepare configuration files" in [Quick Start](../../docs/quick_start.md).



## Baseline

First, we perform federated training without compression, and use this convergence curve as a baseline for comparison with other compression algorithms to verify the difference in convergence efficiency and convergence performance of federated training.

### Experiment

- Run the following command to generate the configuration for the Coordinator and Clients of the federated training:

  ```shell
  python3 example/scripts/gen_config.py \
  --job_name=tf_vgg16
  --workspace=/tmp/nsfl/compression \
  --coordinator_port=8090 \
  --client_ports=9091,9092 \
  --runtime=tensorflow \
  --platform=linux \
  --rounds=20
  ```

  

- Run first Client:

  ```shell
  nvidia-docker run --net host -v /tmp/nsfl/compression:/tmp/nsfl/compression -v ~/.keras/datasets:/root/.keras/datasets nsfl-client-gpu --config_file /tmp/nsfl/compression/client_0/tf_vgg16.json
  ```

  

- Run second Client:

  ```shell
  nvidia-docker run --net host -v /tmp/nsfl/compression:/tmp/nsfl/compression -v ~/.keras/datasets:/root/.keras/datasets nsfl-client-gpu --config_file /tmp/nsfl/compression/client_0/tf_vgg16.json
  ```

  

- Run Coordinator to start federated training:

  ```
  docker run --net host -v /tmp/nsfl/compression:/tmp/nsfl/compression nsfl-coordinator --config_file /tmp/nsfl/compression/coordinator/tf_vgg16.json
  ```



Note：

1. You can also refer to the "Run federated learning" chapter in [Quick Start](../../docs/quick_start.md) to execute in process.
2. Since the official cifar10 dataset of tensorflow does not provide a way to load from the local path, and the directory of the dataset cache is ~/.keras/datasets, so we mount this directory into the container to avoid repeated downloading of the dataset.


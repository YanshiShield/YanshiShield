# FedDC

## Introduction

This article mainly introduces the theory of FedDC, how to use it and the experimental summary.



## Theory

To address data heterogeneity, the [FedDC](https://openaccess.thecvf.com/content/CVPR2022/html/Gao_FedDC_Federated_Learning_With_Non-IID_Data_via_Local_Drift_Decoupling_CVPR_2022_paper.html) introduces lightweight modifications in the local training phase, in which each client utilizes an auxiliary local drift variable to track the gap between the local model parameter and the global model parameters. The key idea of FedDC is to utilize this learned local drift variable to bridge the gap, i.e., conducting consistency in parameter-level.

The more detail to see  [FedDC](https://openaccess.thecvf.com/content/CVPR2022/html/Gao_FedDC_Federated_Learning_With_Non-IID_Data_via_Local_Drift_Decoupling_CVPR_2022_paper.html) paper.



## Experiment

In first experiment, we use 20 clients. The training script is the same as the [source code](https://github.com/gaoliang13/FedDC) of the FedDC paper, and we use the data sampled from drichlet distribution.

* Run the following command to download cifar10 dataset.

```shell
python3 example/data/prepare_torch_data.py \
--path=/tmp/nsfl/cifar10  \
--dataset_name=cifar10
```

- Run the following command to generate the configuration for the Coordinator and Clients of the federated training:

  ```shell
 python3 example/scripts/gen_config.py \
--job_name=torch_cifar10_feddc \
--workspace=/tmp/nsfl/feddc \
--coordinator_port=8090 \
--client_ports=9380,9381,9382,9383,9384,9385,9386,9387,9388,9389,9390,9391,9392,9393,9394,9395,9396,9397,9398,9399 \
--runtime=pytorch \
--platform=linux \
--rounds=60\
--dataset=/tmp/nsfl/cifar10/ \
--dataset_name=cifar10 \
--data_split=drichlet \
--drichlet_arg=0.3 \
--drichlet_seed=20 \
--optionals="{'loss':{'name':'feddc'}}"
  ```



  Note:


  1. Refer to the description of script parameters in the chapter "Prepare configuration files" in [Quick Start](../../../docs/quick_start.md) to configure the "optionals" item.

  2. Refer to [Job Configuration Guide](../../../docs/apis.md), configure the loss in "optionals",  feddc only need to set loss name.



- Run first Client:

  ```shell
nvidia-docker run --net host -v /tmp/nsfl/feddc:/tmp/nsfl/feddc -v /tmp/nsfl/cifar10://tmp/nsfl/cifar10 nsfl-client-gpu --config_file /tmp/nsfl/feddc/client_0/torch_cifar10_feddc.json
  ```

- Run second Client:

  ```shell
nvidia-docker run --net host -v /tmp/nsfl/feddc:/tmp/nsfl/feddc -v /tmp/nsfl/cifar10://tmp/nsfl/cifar10 nsfl-client-gpu --config_file /tmp/nsfl/feddc/client_1/torch_cifar10_feddc.json
  ```

other clients started as same.

- Run Coordinator to start federated training:

  ```shell
docker run --net host -v /tmp/nsfl/feddc:/tmp/nsfl/feddc nsfl-coordinator --config_file /tmp/nsfl/feddc/coordinator/torch_cifar10_feddc.json
  ```



In the second experiment, we randomly selected 15 clients per round for testing, not all 20 clients participating. Other settings are the same as the first experiment. It only needs to modify the client_num and threshold_client_num in the /tmp/nsfl/fedc/cifar10_feddc.json configuration. Set the two values to 15.

## Conclusion

We also run Feddc and Fedavg of the [source code](https://github.com/gaoliang13/FedDC) under the same settings. The nsfl_feddc_client20_d0.3_all is our running result. The origin_fedavg_client20_d0.3_all is running on FedDC's source code with fedavg. and The  origin_feddc_client20_d0.3_all is running on FedDC's source code with FedDC. Experiments show that our FedDC have the same effect with the original papers , and when the number of clients is enough, the FeddC effect is better than Fedavg.

![feddc_result](.\images\feddc_result.png)



The same as above, We also run Feddc and Fedavg of the [source code](https://github.com/gaoliang13/FedDC) under the same settings. The nsfl_feddc_client20_d0.3_participation15 is our running result. The origin_fedavg_client20_d0.3_participation15 is running on FedDC's source code with fedavg. and The  origin_feddc_client20_d0.3_participation15 is running on FedDC's source code with FedDC. Experiments show that our FedDC have the same effect with the original papers , and when selecting part of the client, feddc is still effect.

![feddc_result](.\images\feddc_result2.png)
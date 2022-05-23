
------
**This document will describe the usage and performances of aggregation algorithms in detail.**

**Aggregation algos**:

- [FedAvg](#fedavg)
- [FedProx](#fedprox)
- [SCAFFOLD](#scaffold)

----

### FedAvg

The federated average algorithm performs a weighted average of the model parameters updates of all clients participating in the training in this round, where the weight value is the proportion of the client samples to the total samples.

FedAvg Citing Paper: [Communication-Efficient Learning of Deep Networks from Decentralized Data](https://arxiv.org/pdf/1602.05629.pdf) 

Note: Federated average is one of the earliest proposed federated aggregation algorithms, which is the default standard aggregation algorithm in federated learning and can be used in most normal training situations. But in the face of data heterogeneity(non-IID), it may fails to converge.

#### How to use it

```
We use the FedAvg algorithm by default without any additional configuration.
```

#### Performances

We train on the [Flowers Recognition](https://www.kaggle.com/datasets/alxmamaev/flowers-recognition) dataset, and each client with an IID data distribution, the following figure is the convergence curve with comparison with other algorithms.

| IID                            | non-IID                        |
| ------------------------------ | ------------------------------ |
| ![fedavg1](../images/algorithms/fedavg1.png) | ![fedavg2](../images/algorithms/fedavg2.png) |



### FedProx

The FedProx algorithm limits the influence of local updates by adding correction terms on the local updates, so that the weights of the local model does not deviate from the global model.

FedProx Citing Paper: [FEDERATED OPTIMIZATION IN HETEROGENEOUS NETWORKS](https://arxiv.org/pdf/1812.06127.pdf)

Note: FedProx mainly tackle data heterogeneity in federated learning. It has stronger convergence and more stability on heterogeneous datasets.  In addition, it's a generalized form of FedAvg in essence, when the parameter $\mu$ is 0, the algorithm degenerates to FedAvg. It is very suitable for situations where the client participating in the has the heterogeneous data.

#### How to use it

You can use the FedProx aggregation algorithm by adding 'parameters' configuration to the job configuration file. For example:

```
"parameters": {
    "--optimizer": "fedprox",
    "--mu": 0.6
}
```

#### Performances

We train on the [Flowers Recognition](https://www.kaggle.com/datasets/alxmamaev/flowers-recognition) dataset, and test the federated training both under IID and non-IID respectively, the following figure is the convergence curve with comparison with FedAvg. Convergence will be slower in the IID case, but able to converge in the non-IID case

| IID                              | non-IID                          |
| -------------------------------- | -------------------------------- |
| ![fedprox1](../images/algorithms/fedprox1.png) | ![fedprox2](../images/algorithms/fedprox2.png) |



### SCAFFOLD

The SCAFFOLD algorithm introduce the global and local gradient corrections to correct the deviation caused by the non-IID sample data in the client. So the client's local weights will not deviate from the global weights too large.

SCAFFOLD Citing Paper: [SCAFFOLD: Stochastic Controlled Averaging for Federated Learning](https://arxiv.org/pdf/1910.06378.pdf)

Note: The algorithm also mainly solves the problem of data heterogeneous. The same convergence rate as FedAvg can be achieved even under non-IID. However, it is a stateful algorithm, which means that there are strict requirements for client stability and also system reliability, so it is not very suitable for Cross-Device scenarios.

#### How to use it

You can use the SCAFFOLD aggregation algorithm by adding a 'optimizer 'configuration to the job configuration file. For example:

```
"optimizer": {
    "name": "scaffold",
    "params": {}
}
```

#### Performances

We train on the [Flowers Recognition](https://www.kaggle.com/datasets/alxmamaev/flowers-recognition) dataset, and test the federated training both under IID and non-IID respectively, the following figure is the convergence curve with comparison with FedAvg. Likewise, it converges more slowly in the IID case, but is able to converges in the non-iid case.

| IID                                | non-IID                            |
| ---------------------------------- | ---------------------------------- |
| ![scaffold1](../images/algorithms/scaffold1.png) | ![scaffold2](../images/algorithms/scaffold2.png) |




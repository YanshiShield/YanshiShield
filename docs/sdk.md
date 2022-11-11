
## Client SDK

The SDK provides a way to interact with the federated framework. It is convenient for users to migrate their previous center-based training program to the federated environment with just a few lines of code, which will greatly simplify the development process.

First, you should reference [here](./install.md) to install the SDK Toolkit. Then you can use the SDK in your federated training or evaluating scripts. Here is an example of how to use it:


```python
import neursafe_fl as nsfl

model = Net()  # init your model
nsfl.load_weights(model)  # load federated global model weights
```
We provide the following SDK interfaces.


## Table of Contents

- [SDK](#sdk)
  - [load_weights(model)](#load_weightsmodel)
  - [commit(metrics, trained_model=None, optimizer=None)](#commitmetrics-trained_modelnone-optimizernone)
  - [get_dataset_path(name)](#get_dataset_pathname)
  - [get_parameter(key)](#get_parameterkey)
  - [get_parameters()](#get_parameters)
  - [put_parameter(key, value)](#put_parameterkey-value)
  - [put_parameters(parameters)](#put_parametersparameters)
  - [get_file(filename, dserialize_func=None, **kwargs)](#get_filefilename-dserialize_funcnone-kwargs)
  - [put_file(filename, content, serialize_func=None, **kwargs)](#put_filefilename-content-serialize_funcnone-kwargs)
  - [create_optimizer(**kwargs)](#create_optimizerkwargs)
  - [feddc_loss(model, origin_loss_func, sample_num, batch_size, lr, epoch, alpha=0.01, **kwargs)](#feddc_lossmodel-origin_loss_func-sample_num-batch_size-lr-epoch-alpha_0.01-kwargs)


## SDK

### load_weights(model)

- Description: load the global weights, which broadcast from the server.

  ```
  The global weights is broadcast to all the clients by server when each federated round starts. the client will load this global weights as the init weights for training or evaluating.
  Current we support tf and torch runtimes, so you use the models of these two runtimes.
  ```

- inputs:

  | name  | type                    | required | description                                            |
  | ----- | ----------------------- | -------- | ------------------------------------------------------ |
  | model | tf model<br>torch model | yes      | the local training model, supporting tf or torch model |

- outputs:

  None



### commit(metrics, trained_model=None, optimizer=None)

- Description: Commit delta weights and metrics  to server.

  ```
  Commit local trained weights to federated framework by this interface, and the framework will calculate delta weights(the difference between local weights and the global weights) before send it to server. And after local training or evaluating finished, typically there will be some metrics for server to analysis, such as loss, acccury. You can use this interface to directly send the metrics to server.
  ```

- inputs:

  | name          | type                    | required | description                                                  |
  | ------------- | ----------------------- | -------- | ------------------------------------------------------------ |
  | metrics       | dict                    | yes      | A dictionary stored the metrics data after train or evaluate. For example, the dict keys could include:<br>- sample_num int32,<br/>- spend_time int32,<br/>- loss float,<br/>- accuracy float,<br/>- precision float,<br/>- recall_rate float<br>or other values. |
  | trained_model | tf model<br>torch model | no       | the local training model, supporting tf or torch model. It's not must set in evaluate round. |
  | optimizer     | object(optimizer)       | no       | the optimizer object instance used in local training, supporting tf or torch optimizer |

- outputs:

  None




### get_dataset_path(name)

- Description: Get the path of the dataset by the dataset name.

  ```
  In federated learning scene, the dataset store in clients. So when client setup, it will load dataset's mapping configuration file, which map the dataset name to the dataset path.
  Then when the federated job starts, it could get the dataset through this interface.
  ```

- inputs:

  | name | type   | required | description                                                  |
  | ---- | ------ | -------- | ------------------------------------------------------------ |
  | name | string | yes      | A index name of the dataset you want to obtain for local training, the path of dataset is from configuration file. |

- outputs:

  path(string): the path to store the dataset.



### get_parameter(key)

- Description: Get a parameter from server.

  ```
  The parameters is defined in coordinator extender config, which is user self-deined.
  Coordinator will broadcast them to clients. and user can get one of these parameters through this interface.
  The parameters are organized as dict, get it through its key.
  ```

- inputs:

  | name | type   | required | description          |
  | ---- | ------ | -------- | -------------------- |
  | key  | string | yes      | The key of parameter |

- outputs:

  Value: return the value of the parameter, None if key not exist.



### get_parameters()

- Description: Get all the parameters from the server.

  ```
  The parameters is defined in coordinator extender config, which is user self-deined.
  Coordinator will broadcast them to clients. and user can get these parameters through this interface.
  The parameters are organized as dict, return all parameters as a dict.
  ```

- inputs:

  None

- outputs:

  Parameters(dict): return all the parameters as a dict.


### put_parameter(key, value)

- Description: Put a parameter to server.

  ```
  The parameters, which generated in the local task, will be sent to server by this interface. Typically used for user self-defined aggregation, some calculations require additional parameters.
  Note that using this will append the parameter to old ones if you call this function several times. All the parameters will be organized as a dict to sent server.
  ```

- inputs:

  | name  | type   | required | description            |
  | ----- | ------ | -------- | ---------------------- |
  | key   | string | yes      | The key of parameter   |
  | value | --     | yes      | The value of parameter |

- outputs:

  None



### put_parameters(parameters)

- Description: Put paramters to server, which parameters is already organized as a dict.

  ```
  The parameters, which generated in the local task, will be sent to server by this interface. Typically used for user self-defined aggregation, some calculations require additional parameters.
  Note that this interface require parameters to be organized as a dict. It's similar to put_paramter().
  ```

- inputs:

  | name       | type | required | description                             |
  | ---------- | ---- | -------- | --------------------------------------- |
  | parameters | dict | yes      | all the parameters organized as a dict. |

- outputs:

  None



### get_file(filename, dserialize_func=None, **kwargs)

- Description: Get a file from server.

  ```
  The files should be defined in coordinator extender config, which is user-defined. The Coordinator will broadcast these files to the clients, then you can get the file through this interface. Typically used for user-defined calculations.
  If you have several files, you should call this function several times.
  ```

- inputs:

  | name            | type     | required | description                                                  |
  | --------------- | -------- | -------- | ------------------------------------------------------------ |
  | filename        | string   | yes      | the name of file you want to get                             |
  | dserialize_func | function | no       | if need, you can pass a function that used to deserialize the file content |
  | kwargs          | dict     | no       | arguments need to pass to the dserialize function            |

- outputs:

  data: the content of the file (after dserialize if need)



### put_file(filename, content, serialize_func=None, **kwargs)

- Description: Put a file to server.

  ```
  The files, which generated in the local task can be sent to server by this interface, typically used for user-defined aggregation.
  ```

- inputs:

  | name           | type     | required | description                                                 |
  | -------------- | -------- | -------- | ----------------------------------------------------------- |
  | filename       | string   | yes      | the file name                                               |
  | content        | --       | yes      | the content of the file                                     |
  | serialize_func | function | no       | if need pass a function to serializethe content before send |
  | kwargs         | dict     | no       | arguments need to pass to the serialize function            |

- outputs:

  None



### create_optimizer(**kwargs)

- Description: Create an optimizer specific to Federated Learning

  ```
  Here are some optimizers for federated learning, such as fedProx, SCAFFOLD etc. And it could be more helpful than tranditonal optimizers in some specific areas.
  Current we support fedProx, SCAFFOLD, which is able to converge under Non-IID circumstances.
  ```

- inputs:

  | name   | type | required | description                                                  |
  | ------ | ---- | -------- | ------------------------------------------------------------ |
  | kwargs | dict | no       | parameters that need to pass the optimzier for initialization |

- outputs:

  return an instance of optimizer object.

### feddc_loss(model, origin_loss_func, sample_num, batch_size, lr, epoch, alpha=0.01, **kwargs)

- Description: Get an feddc loss to Federated Learning

  ```
  FedDC is able to converge under Non-IID circumstances.
  ```

- inputs:

  | name        | type           | property | algorithm | description                                                  |
  | ----------- | -------------- | -------- | --------- | ------------------------------------------------------------ |
  | model | tf/torch model | required | feddc     | The model will be using to train. and it already loaded init weights from coordinator. |
  | origin_loss_func | func | optional | feddc     | Base loss function used for train. Default is CrossEntropyLoss in pytorch, the same as categorical_crossentropy in tensorflow. |
  | sample_num  | int            | optional | feddc     | The number of samples used in this round when training the local model |
  | batch_size  | int            | optional | feddc     | The batch size used when training the local model            |
  | lr          | float          | optional | feddc     | Local training learning rate                                 |
  | epoch       | int            | optional | feddc     | The epoch used when training the local model                 |
  | alpha       | float          | optional | feddc     | The hyper-parameter that controls the weight of R, The recommended setting value is 0.1、0.01、0.005. |

  kwargs:

  | name             | type | property | algorithm | description                                                  |
  | ---------------- | ---- | -------- | --------- | ------------------------------------------------------------ |
  | device           | str  | optional | feddc     | Use cpu or gpu when run training, only used in pytorch.      |
  | print_loss       | int  | optional | feddc     | Printing detail loss per forward or per call.                |

- outputs:

  return an instance of feddc object.


#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint: disable=arguments-differ, too-many-instance-attributes
# pylint: disable=no-member, invalid-name, too-many-arguments, no-name-in-module
"""This implement scaffold optimizer in 'tf.keras'.

Scaffold is an optimizer that use control variates to guarantee the convergence
when data is unbalanced(non-iid).
    global control variates: coordinator broadcast to each client to control the
                             local gradient changes.
    local control variates: gradient state of client in the last round, kept in
                            local device.
"""
import os
import numpy as np
from tensorflow.python.keras.optimizer_v2 import optimizer_v2
from tensorflow.python.ops import resource_variable_ops
from tensorflow.python.training import training_ops
from tensorflow.python.util.tf_export import keras_export
from neursafe_fl.python.libs.optimizer.tensorflow.utils import \
    subtract_variables, add_variables, multiply
from neursafe_fl.python.sdk.custom import get_file, put_file
from neursafe_fl.python.sdk.utils import get_worker_id


def _get_worker_id_prefix():
    worker_id = get_worker_id()
    worker_id_splited = worker_id.split("-")
    worker_id_prefix = "-".join(worker_id_splited[:-3]) + "-"
    return worker_id_prefix


# The local control_variates file path
if os.getenv("CONTROL_VARIATES"):
    local_control_variates_path = os.getenv("CONTROL_VARIATES")
else:
    local_control_variates_path = "/tmp/%slocal_variates.npy" % \
                                  _get_worker_id_prefix()


@keras_export("keras.optimizers.Scaffold")
class Scaffold(optimizer_v2.OptimizerV2):
    """Scaffold Optimizer."""

    _instance = None

    @classmethod
    def get_instance(cls, *args, **kwargs):
        """Get scaffold optimizer instance.
        """
        if not cls._instance:
            cls._instance = Scaffold(*args, **kwargs)
        return cls._instance

    def __init__(self, model_params=None, lr=0.01, batch_size=None,
                 sample_num=None, name="scaffold", **kwargs):
        super().__init__(name, **kwargs)
        self._set_hyper("learning_rate", lr)
        self._set_hyper("decay", self._initial_decay)
        self._local_variate = None
        self._global_variate = None
        self._batch_size = batch_size
        self._sample_num = sample_num

        self._dense_count = 0
        self._sparse_count = 0
        self._local_lr = lr

        self._init_control_variates(model_params)

    def _create_slots(self, var_list):
        for var in var_list:
            self.add_slot(var, "l_ctl_var")
        for var in var_list:
            self.add_slot(var, "g_ctl_var")

    def _resource_apply_dense(self, grad, var, apply_state):
        var_device, var_dtype = var.device, var.dtype.base_dtype
        coefficients = ((apply_state or {}).get((var_device, var_dtype))
                        or self._fallback_apply_state(var_device, var_dtype))

        l_var = self.get_slot(var, 'l_ctl_var')
        val_1 = self._local_variate[self._dense_count %
                                    len(self._local_variate)]
        g_var = self.get_slot(var, 'g_ctl_var')
        val_2 = self._global_variate[self._dense_count %
                                     len(self._global_variate)]
        control_variate = (g_var + val_2 - l_var - val_1)
        grad += control_variate
        self._dense_count += 1

        return training_ops.resource_apply_gradient_descent(
            var.handle, coefficients["lr_t"], grad,
            use_locking=self._use_locking)

    def _resource_apply_sparse_duplicate_indices(self, grad, var, indices,
                                                 **kwargs):
        var_device, var_dtype = var.device, var.dtype.base_dtype
        coefficients = (kwargs.get("apply_state", {}).get((var_device,
                                                           var_dtype))
                        or self._fallback_apply_state(var_device, var_dtype))

        return resource_variable_ops.resource_scatter_add(
            var.handle, indices, -grad * coefficients["lr_t"])

    def _resource_apply_sparse(self, grad, var, indices, apply_state):
        var_device, var_dtype = var.device, var.dtype.base_dtype
        coefficients = ((apply_state or {}).get((var_device, var_dtype))
                        or self._fallback_apply_state(var_device, var_dtype))

        l_var = self.get_slot(var, 'l_ctl_var')
        val_1 = self._local_variate[self._sparse_count %
                                    len(self._local_variate)]
        g_var = self.get_slot(var, 'g_ctl_var')
        val_2 = self._global_variate[self._sparse_count %
                                     len(self._global_variate)]
        control_variate = (g_var + val_2 - l_var - val_1)
        grad += control_variate
        self._sparse_count += 1

        return resource_variable_ops.resource_scatter_add(
            var.handle, indices, -grad * coefficients["lr_t"])

    def get_config(self):
        config = super().get_config()
        config.update({
            "learning_rate": self._serialize_hyperparameter("learning_rate"),
            "decay": self._serialize_hyperparameter("decay"),
        })
        return config

    def _init_control_variates(self, model_params):
        """Init optimizer global and local control variates.

        The global control variates is from server.
        The local control variates is stored in client's local disk.
        """
        # load local control variates and global control variates
        if not os.path.exists(local_control_variates_path):
            local_c = [0 for _ in model_params]
        else:
            local_c = np.load(local_control_variates_path, allow_pickle=True)

        global_control_variates_path = "global_variates.npy"
        try:
            server_c = get_file(global_control_variates_path,
                                dserialize_func=np.load, allow_pickle=True)
        except (OSError, KeyError):
            server_c = [0 for _ in model_params]

        self._global_variate = server_c
        self._local_variate = local_c

    def _update_control_variates(self, model):
        """Update the local variates after training.

        Args:
            fl model: the fl model used to train.
        """
        trainable_y = model.weights
        trainable_x = model.init_weights

        # compute new local control variates, and save for next round.
        tmp1 = subtract_variables(self._local_variate, self._global_variate)
        tmp2 = subtract_variables(trainable_x, trainable_y)
        local_steps = self._sample_num / self._batch_size
        tmp2 = multiply(tmp2, (1 / local_steps * self._local_lr))
        new_local_c = add_variables(tmp1, tmp2)
        np.save(local_control_variates_path, new_local_c)

        # compute delta local control variates, save to file for uploading.
        delta_c = subtract_variables(new_local_c, self._local_variate)
        put_file("delta_control_variates.npy", delta_c, serialize_func=np.save)

    def update(self, model):
        """Update local control variates for scaffold.
        """
        self._update_control_variates(model)

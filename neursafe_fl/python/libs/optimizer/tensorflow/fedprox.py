#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint: disable=arguments-differ, no-name-in-module
"""FedProx Optimizer algorithm."""
from tensorflow.python.keras.optimizer_v2 import optimizer_v2
from tensorflow.python.ops import array_ops
from tensorflow.python.ops import resource_variable_ops
from tensorflow.python.training import training_ops


class PerturbedGradientDescentError(Exception):
    """PerturbedGradientDescent optimizer exception."""


class PerturbedGradientDescent(optimizer_v2.OptimizerV2):
    """This optimizer can handle with no-iid data.

    Optimizer abbreviation: FedProx.

    ARGS:
        learning rate: The base learning rate
        mu: A hyper parameter which adjust gradient descent
        origin trainable weights: initial model weights
    """
    def __init__(self,
                 learning_rate=0.01,
                 mu=0,
                 origin_trainable_weights=None,
                 name="PerturbedGradientDescent",
                 **kwargs):
        super().__init__(name, **kwargs)
        self._set_hyper("learning_rate", learning_rate)
        self._set_hyper("prox_mu", mu)
        self.__origin_trainable_weights = origin_trainable_weights
        self.__slot_inited = False

        self.__check_parameter()

    def __check_parameter(self):
        if not isinstance(self.__origin_trainable_weights, list):
            err_msg = 'origin trainable weights not list.'
            raise PerturbedGradientDescentError('Optimizer error: %s' % err_msg)

    def _create_slots(self, var_list):
        if not self.__slot_inited:
            for var in var_list:
                self.add_slot(var, "vstar")
                self.__slot_inited = True

    def _prepare_local(self, var_device, var_dtype, apply_state):
        if "learning_rate" in self._hyper:
            lr_t = array_ops.identity(self._decayed_lr(var_dtype))
            apply_state[(var_device, var_dtype)]["lr_t"] = lr_t

        if "prox_mu" in self._hyper:
            mu_t = array_ops.identity(self._decayed_lr(var_dtype))
            apply_state[(var_device, var_dtype)]["mu_t"] = mu_t

        self._create_slots(self.__origin_trainable_weights)

    def _resource_apply_dense(self, grad, var, apply_state=None):
        var_device, var_dtype = var.device, var.dtype.base_dtype
        coefficients = ((apply_state or {}).get((var_device, var_dtype))
                        or self._fallback_apply_state(var_device, var_dtype))

        vstar = self.get_slot(var, "vstar")
        grad += coefficients["mu_t"] * (var - vstar)

        return training_ops.resource_apply_gradient_descent(
            var.handle, coefficients["lr_t"], grad,
            use_locking=self._use_locking)

    def _resource_apply_sparse_duplicate_indices(self, grad, var, indices,
                                                 **kwargs):
        var_device, var_dtype = var.device, var.dtype.base_dtype
        coefficients = (kwargs.get("apply_state", {}).get((var_device,
                                                           var_dtype))
                        or self._fallback_apply_state(var_device, var_dtype))

        vstar = self.get_slot(var, "vstar")
        grad += coefficients["mu_t"] * (var - vstar)

        return resource_variable_ops.resource_scatter_add(
            var.handle, indices, -grad * coefficients["lr_t"])

    def _resource_apply_sparse(self, grad, var, indices, apply_state=None):
        # This method is only needed for momentum optimization.
        var_device, var_dtype = var.device, var.dtype.base_dtype
        coefficients = ((apply_state or {}).get((var_device, var_dtype))
                        or self._fallback_apply_state(var_device, var_dtype))

        vstar = self.get_slot(var, "vstar")
        grad += coefficients["mu_t"] * (var - vstar)

        return resource_variable_ops.resource_scatter_add(
            var.handle, indices, -grad * coefficients["lr_t"])

    def get_config(self):
        config = super().get_config()
        config.update({
            "learning_rate": self._serialize_hyperparameter("learning_rate"),
            "prox_mu": self._serialize_hyperparameter("prox_mu"),
        })
        return config

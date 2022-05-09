#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Federate Learning Model Manage Module."""


from neursafe_fl.python.runtime.runtime_factory import RuntimeFactory


class FlModel:
    """Federated Model class.

    Model manages and operates the global(server) model, and also provides
    a unified interface for different low-level backend runtime.
    Currently support tensorflow and pytorch.
    Notices:
        pytorch: only support operates on weights, model is None.

    Attributes:
        __model: global model(aggregated model) in server
        __weights: global weights(aggregated weights) of the model
    """

    def __init__(self, model_path, runtime):
        self.__model_path = model_path
        self.__runtime = runtime
        self.__model = None  # global model
        self.__weights = None  # global weights
        self.__calculator = None

    def load(self):
        """Load init server model from model_path."""
        calculator = RuntimeFactory.create_weights_calculator(self.__runtime)
        self.__calculator = calculator
        self.__model = RuntimeFactory.create_model(self.__runtime)
        self.__weights = self.__model.load(self.__model_path,
                                           return_type="weights")

    def get_weights(self):
        """Get the global(server) model weights."""
        return self.__weights

    def set_weights(self, weights):
        """Set global(server) model weights."""
        self.__weights = weights

    def load_model(self, path):
        """Load model from path."""
        return self.__model.load(path)

    def save_model(self, path):
        """Save the model to path."""
        self.__model.save(self.__weights, path, save_type="model")

    def load_weights(self, path):
        """Load weights from path."""
        return self.__model.load(path, load_type="weights",
                                 return_type="weights")

    def save_weights(self, path):
        """Save the weights to path."""
        self.__model.save(self.__weights, path)

    def add_delta_weights(self, delta_weights):
        """Add delta weights to the current global weights.

        This operation actually updates the weights after each round of
        aggregation to the server model.

        Args:
            delta_weights: Aggregated weights of all the clients of one round.
                           The difference between the weights of the previous
                           round.
        """
        self.__weights = self.__calculator.add(self.__weights, delta_weights)

    @property
    def runtime(self):
        """Return the runtime of model."""
        return self.__runtime

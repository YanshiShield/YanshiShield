#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=super-init-not-called, too-few-public-methods
"""
Different kind resource class definition
"""


class Resource:
    """Base resource class
    """
    def __init__(self, volume):
        self.name = None
        self.volume = volume
        self.allocated = 0


class GPU(Resource):
    """Cpu resource class
    """
    def __init__(self, volume):
        self.name = "gpu"
        self.volume = volume
        self.allocated = 0


class CPU(Resource):
    """Gpu resource class
    """
    def __init__(self, volume):
        self.name = "cpu"
        self.volume = volume
        self.allocated = 0.0


class Memory(Resource):
    """Memory resource class, unit is MB.
    """
    def __init__(self, volume):
        self.name = "memory"
        self.volume = volume
        self.allocated = 0

#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""The posix interface
"""

import os
import shutil
from neursafe_fl.python.model_manager.storage.base_io import StorageInterface,\
    PathNotExist


class PosixClient(StorageInterface):
    """Posix storage interface implementation.
    """

    def __init__(self, **kwargs):
        self.root_path = kwargs.get("root_path")

    def copy(self, src, target, callback=None):
        """The copy operation of posix interface.

        If the self.root_path is None, the src and target is the absolute path.
        Otherwise the src and target is the child path under the self.root_path.
        """
        _src = "%s/%s" % (src["namespace"], src["path"].lstrip("/"))
        _target = "%s/%s" % (target["namespace"], target["path"].lstrip("/"))
        if self.root_path:
            _src = os.path.join(self.root_path, _src)
            _target = os.path.join(self.root_path, _target)

        if not os.path.exists(_src):
            raise PathNotExist("Src %s not exist." % _src)

        target_parent = os.path.dirname(_target)
        if not os.path.exists(target_parent):
            os.makedirs(target_parent)

        shutil.copy(_src, _target)

    def delete(self, target, callback=None):
        """The delete operation of posix interface.
        """
        _target = "%s/%s" % (target["namespace"], target["path"].lstrip("/"))
        if self.root_path:
            _target = os.path.join(self.root_path, _target)

        if not os.path.exists(_target):
            raise PathNotExist("Target %s not exist." % _target)

        if os.path.isdir(_target):
            shutil.rmtree(_target)
        else:
            os.remove(_target)

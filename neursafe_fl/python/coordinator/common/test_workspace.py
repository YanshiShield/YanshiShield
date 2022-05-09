#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=missing-function-docstring
"""Workspace UnitTest."""
import os
import shutil
import unittest
import tempfile

from neursafe_fl.python.coordinator.common.workspace import Workspace, Files


class TestWorkspace(unittest.TestCase):
    """Test class."""

    def setUp(self) -> None:
        self.output = tempfile.mkdtemp()
        self.job_name = "unittest_fl"
        self._temp_dir = None

    def tearDown(self) -> None:
        # delete the test dir.
        if os.path.exists(self.output):
            shutil.rmtree(self.output)
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)

    def test_should_create_job_dir_success(self):
        workspace = Workspace(self.output, self.job_name)
        job_dir = workspace.get_job_dir()
        correct_dir = os.path.join(self.output,
                                   "fl_%s_output_V0" % self.job_name)
        self.assertEqual(job_dir, correct_dir)

    def test_should_create_temp_dir_success(self):
        workspace = Workspace(self.output, self.job_name)
        temp_dir = workspace.get_tmp_dir()
        self.assertTrue(temp_dir.startswith("/tmp"))
        self.assertTrue(os.path.exists(temp_dir))
        self._temp_dir = temp_dir

    def test_should_create_round_dir_success(self):
        workspace = Workspace(self.output, self.job_name)
        temp_dir = workspace.get_tmp_dir()
        round_dir = workspace.get_round_dir(10)
        self.assertTrue(round_dir.startswith(temp_dir))
        self.assertTrue(round_dir.endswith("10"))
        self._temp_dir = temp_dir

    def test_should_create_client_upload_dir_success(self):
        workspace = Workspace(self.output, self.job_name)
        round_dir = workspace.get_round_dir(round_id=5)
        client_dir = workspace.get_client_upload_dir(round_id=5, client_id=1)
        self.assertTrue(client_dir.startswith(round_dir))
        self._temp_dir = workspace.get_tmp_dir()

    def test_should_get_runtime_file_success(self):
        workspace = Workspace(self.output, self.job_name)
        file_name = workspace.get_runtime_file_by(Files.InitWeights,
                                                  runtime="tensorflow")
        self.assertTrue(file_name.endswith(".h5"))

        file_name = workspace.get_runtime_file_by(Files.Checkpoint,
                                                  runtime="pytorch")
        self.assertTrue(file_name.endswith(".pth"))

    def test_should_get_runtime_file_without_suffix_when_runtime_not_support(self):
        workspace = Workspace(self.output, self.job_name)
        file_name = workspace.get_runtime_file_by(Files.Checkpoint,
                                                  runtime="caffe")
        self.assertEqual(file_name, Files.Checkpoint)

    def test_should_created_job_dir_success_when_job_dir_already_exist(self):
        workspace = Workspace(self.output, self.job_name)
        job_dir_1 = workspace.get_job_dir()
        correct_dir = os.path.join(self.output,
                                   "fl_%s_output_V0" % self.job_name)
        self.assertEqual(job_dir_1, correct_dir)

        workspace_2 = Workspace(self.output, self.job_name)
        job_dir_2 = workspace_2.get_job_dir()
        correct_dir = os.path.join(self.output,
                                   "fl_%s_output_V1" % self.job_name)
        self.assertEqual(job_dir_2, correct_dir)


if __name__ == "__main__":
    unittest.main()

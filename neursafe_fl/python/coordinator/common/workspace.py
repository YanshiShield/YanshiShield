#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""Workspace(File and Directory) Manage Module."""

import os
import re
import random
import string
import json

from absl import logging

from neursafe_fl.python.coordinator.common.utils import runtime_suffix
from neursafe_fl.python.coordinator.common.const import CKPT_ROOT_PATH,\
    COORDINATOR_WORKSPACE_PATH, DEPLOYMENT_WAY


CHECKPOINT_FILE_PREFIX = "checkpoint_v"


class Files:  # pylint:disable=too-few-public-methods
    """Runtime files for training process."""
    InitWeights = "init_weights"
    RoundUpdates = "round_updates"
    AggregatedWeights = "aggregated_weights"
    Checkpoint = "checkpoint"
    FinalModel = "final_model"
    ZipPackage = "fed_files.zip"


class Workspace:
    """Manage the dirs and files in the federate learning process.

    All the files and dir generated during the federate job, should be defined
    in this class, which provide method to get.
    Mainly including Output directory and Temp directory. The Output directory
    will be retained and the Temp directory will be deleted after the job
    finished.

    Attributes:
        __output_dir: the path to saved outputs, which will be used to save
                      training result, model, visualize data etc.
        __job_dir: Save directory, used to persist some necessary files during
                   the process, such as metrics, models.
        __tmp_dir: Temp directory save the necessary temp files(in /tmp) for
                   training process.
    """

    def __init__(self, output, job_name):
        self.__output_dir = output if output else os.getcwd()
        self.__job_name = job_name
        self.__job_dir = None
        self.__tmp_dir = None
        self.__job_v = 0
        self.__ckpt_root_dir = None

    def get_checkpoints(self):
        """Return all checkpoints info"""
        ckpts = {}
        dirs = os.listdir(self.__output_dir)
        job_dir_pattern = "fl_%s_output_V*" % self.__job_name
        ckpt_id_pattern = "%s(.*)" % CHECKPOINT_FILE_PREFIX
        max_ckpt_id = 0

        for dir_name in dirs:
            if re.search(job_dir_pattern, dir_name):
                ckpt_root_dir = os.path.join(self.__output_dir,
                                             dir_name,
                                             CKPT_ROOT_PATH)
                ckpts.update(self.__get_ckpts(ckpt_root_dir))

        for ckpt_id in list(ckpts.keys()):
            res = re.search(ckpt_id_pattern, ckpt_id)
            if res and int(res.group(1)) > max_ckpt_id:
                max_ckpt_id = int(res.group(1))

        return ckpts, max_ckpt_id

    def __get_ckpts(self, ckpt_root_path):
        if not os.path.exists(ckpt_root_path):
            return {}

        ckpt_dir_pattern = "%s*" % CHECKPOINT_FILE_PREFIX
        dirs = os.listdir(ckpt_root_path)
        ckpts = {}

        for dir_name in dirs:
            if re.search(ckpt_dir_pattern, dir_name):
                ckpt_dir = os.path.join(ckpt_root_path, dir_name)
                ckpt_id = dir_name
                ckpt_info = self.__get_ckpt(ckpt_dir)
                if ckpt_info:
                    ckpts[ckpt_id] = ckpt_info

        return ckpts

    def __get_ckpt(self, ckpt_path):
        try:
            ckpt_pattern = "checkpoint*"
            metrics_file = "metrics.json"
            dirs = os.listdir(ckpt_path)
            ckpt_file_path = None

            for dir_name in dirs:
                if (re.search(ckpt_pattern, dir_name)
                        and os.path.isfile(os.path.join(ckpt_path, dir_name))):
                    ckpt_file_path = os.path.join(ckpt_path, dir_name)

            with open(os.path.join(ckpt_path, metrics_file)) as f:
                res = json.load(f)
                accuracy = res.get("accuracy")

            if accuracy and ckpt_file_path:
                if DEPLOYMENT_WAY == "cloud":
                    ckpt_file_path = ckpt_file_path.lstrip(
                        COORDINATOR_WORKSPACE_PATH)
                return {"path": ckpt_file_path,
                        "accuracy": accuracy}

            return None
        except Exception as err:
            logging.exception(str(err))
            return None

    def get_round_dir(self, round_id):
        """Get the round directory.

        Each round has an independent directory under the tmp dir, saving the
        updates, aggregate result and other files during this round.
        It will be deleted after round finished.
        """
        if not self.__tmp_dir:
            self.__tmp_dir = self._create_tmp_dir()
        round_dir = os.path.join(self.__tmp_dir, "round_%s" % round_id)
        if not os.path.exists(round_dir):
            os.mkdir(round_dir)
        return round_dir

    def get_job_dir(self):
        """Get the output directory of the job."""
        if not self.__job_dir:
            self.__job_dir = self._create_job_dir()
        return self.__job_dir

    def __create_ckpt_root_dir(self):
        ckpt_root_dir = os.path.join(self.__output_dir,
                                     self.__job_dir,
                                     CKPT_ROOT_PATH)
        if os.path.exists(ckpt_root_dir):
            return ckpt_root_dir

        os.mkdir(ckpt_root_dir)
        return ckpt_root_dir

    def create_ckpt_dir(self, ckpt_id):
        """Return checkpoint directory of the job"""
        if not self.__job_dir:
            self.__job_dir = self._create_job_dir()

        if not self.__ckpt_root_dir:
            self.__ckpt_root_dir = self.__create_ckpt_root_dir()

        name = "V%s_%s%s" % (self.__job_v, CHECKPOINT_FILE_PREFIX, ckpt_id)
        ckpt_dir = os.path.join(self.__output_dir,
                                self.__job_dir,
                                CKPT_ROOT_PATH,
                                name)

        if not os.path.exists(ckpt_dir):
            os.mkdir(ckpt_dir)

        return name, ckpt_dir

    def _create_job_dir(self, version=0):
        job_dir = os.path.join(self.__output_dir,
                               "fl_%s_output_V%s" % (self.__job_name, version))
        if os.path.exists(job_dir):
            return self._create_job_dir(version=version + 1)
        self.__job_v = version
        os.mkdir(job_dir)
        return job_dir

    def get_tmp_dir(self):
        """Get temporary dir for this job under the /tmp."""
        if not self.__tmp_dir:
            self.__tmp_dir = self._create_tmp_dir()
        return self.__tmp_dir

    def _create_tmp_dir(self):
        random_str = ''.join(
            random.sample(string.ascii_letters + string.digits, 8))
        tmp_work_dir = "/tmp/fl_%s_%s" % (self.__job_name, random_str)
        if os.path.exists(tmp_work_dir):
            return self._create_tmp_dir()
        os.mkdir(tmp_work_dir)
        return tmp_work_dir

    def get_client_upload_dir(self, round_id, client_id):
        """Dir for client upload updates.

        During the round execution, if each client has one independent dir to
        save files, should be created a dir under the round dir.

        Args:
            round_id: the current round number.
            client_id: the number of client upload to this round.
        """
        round_dir = self.get_round_dir(round_id)
        upload_dir = os.path.join(round_dir, "client_%s" % client_id)
        if not os.path.exists(upload_dir):
            os.mkdir(upload_dir)
        return upload_dir

    def get_runtime_file_by(self, filename, runtime, number=None):
        """Get the full name of the runtime file.

        Runtime Files is the intermediate files needed for the training process.
        Different runtime(model) may use different file suffix.

        Args:
            filename: runtime filename belong in Files(without suffix, id).
            runtime: the model runtime, tensorflow, pytorch.
            number: Add serial number to the file name.
        Returns:
            full name of the runtime file, such as init_weight.h5,
            final_weight.pth, checkpoint_2.h5 etc.
        """
        suffix = runtime_suffix(runtime)
        if not number:
            return ''.join([filename, suffix])
        full_name = '%s_%s' % (filename, number)
        return ''.join([full_name, suffix])

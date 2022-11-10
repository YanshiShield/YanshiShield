#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
Generate all fl configs.
"""
import logging
import ast
import os
import json

from absl import app
from absl import flags
from shutil import copyfile, move
from subprocess import call

from data_util import gen_drichlet_distribution_data

FORMAT = ("[%(asctime)s] %(filename)s"
          "[line:%(lineno)d] %(levelname)s: %(message)s")
logging.basicConfig(format=(FORMAT), level="INFO")


flags.DEFINE_string("workspace", None, "Root dir for generating config files")
flags.DEFINE_string("coordinator_port", None, "Coordinator service port.")
flags.DEFINE_string("client_ports",
                    None,
                    "Clients service port, the clients number same with ports"
                    "number.")
flags.DEFINE_string("runtime", None, "FL job executing runtime.")
flags.DEFINE_string("platform", None, "FL job run on which platform.")
flags.DEFINE_string("job_name", None, "Fl job name.")
flags.DEFINE_string("rounds", None, "FL job rounds num.")
flags.DEFINE_string("dataset", None, "Dataset directory or path.")
flags.DEFINE_string("data_split", "index",
                    "Split the data by [index, class, drichlet]. The index, "
                    "data will be evenly divided into each client. The class, "
                    "data will be divided into each client according to the "
                    "category. The drichlet, data will be sampled from the "
                    "drichlet distribution.")
flags.DEFINE_string("dataset_name", None,
                    "The Dataset for drichlet sample. It's effective when "
                    "data_split set drichlet.")
flags.DEFINE_float("drichlet_arg", 0.3,
                   "The parameter for drichlet distribution, lower drichlet_arg "
                   "and higher heterogeneity.")
flags.DEFINE_integer("drichlet_seed", 20,
                     "The random seed for drichlet distribution. When use same "
                     "seed, The generated data distribution is the same.")
flags.DEFINE_string("optionals", None, "Optional configs, such as: "
                                       "secure algorithm, compression")


FLAGS = flags.FLAGS


current_dir = os.getcwd()


def _gen_client_addresses():
    addresses = []
    for port in FLAGS.client_ports.split(","):
        addresses.append("127.0.0.1:%s" % port)

    return ",".join(addresses), len(addresses)


def _gen_init_model_path(coordinator_root_dir):
    job_dir = os.path.join(current_dir, "example/jobs/%s" % FLAGS.job_name)

    def gen_init_model():
        script_file = os.path.join(job_dir, "gen_init_model.py")
        os.chdir(job_dir)
        call(["python3", script_file])
        os.chdir(current_dir)

    gen_init_model()

    for file_name in os.listdir(job_dir):
        if file_name.startswith(FLAGS.job_name) and (
                file_name.endswith("h5") or file_name.endswith("pth")):
            model_path = os.path.join(
                coordinator_root_dir,
                "%s%s" % (FLAGS.job_name, os.path.splitext(file_name)[-1]))
            move(os.path.join(job_dir, file_name), model_path)

            return model_path

    return None


def _gen_coordinator_output(coordinator_root_dir):
    path = os.path.join(coordinator_root_dir, FLAGS.job_name)
    _create_dir(path)

    return path


def _gen_coordinator_setup_config():
    # create coordinator root dir
    coordinator_root_dir = os.path.join(FLAGS.workspace, "coordinator")
    _create_dir(coordinator_root_dir)

    # gen setup config
    config_template_path = os.path.join(
        current_dir,
        "example/setup_configs/coordinator.json")

    with open(config_template_path) as f:
        config = json.load(f)

    config["job_name"] = FLAGS.job_name.replace("_", "-")
    config["port"] = int(FLAGS.coordinator_port)
    config["clients"], client_nums = _gen_client_addresses()
    config["model_path"] = _gen_init_model_path(coordinator_root_dir)
    config["runtime"] = FLAGS.runtime
    config["task_entry"] = FLAGS.job_name
    config["output"] = _gen_coordinator_output(coordinator_root_dir)
    config["hyper_parameters"]["max_round_num"] = int(FLAGS.rounds)
    config["hyper_parameters"]["client_num"] = client_nums
    config["hyper_parameters"]["threshold_client_num"] = client_nums

    if FLAGS.optionals:
        config.update(ast.literal_eval(FLAGS.optionals))

    # write new setup config
    with open(os.path.join(coordinator_root_dir,
                           "%s.json" % FLAGS.job_name), "w") as f:
        json.dump(config, f)


def _gen_clients_config():
    for i, port in enumerate(FLAGS.client_ports.split(",")):
        client_root_dir = os.path.join(FLAGS.workspace, "client_%s" % i)
        _gen_client_setup_config(client_root_dir, i, port)
        _gen_scripts(client_root_dir)


def _gen_client_setup_config(client_root_dir, index, port):
    # create client root dir
    _create_dir(client_root_dir)

    # gen setup config
    config_template_path = os.path.join(
        current_dir,
        "example/setup_configs/client.json")

    with open(config_template_path) as f:
        config = json.load(f)

    config["port"] = int(port)
    config["workspace"] = _gen_client_workspace(client_root_dir)
    config["server"] = "127.0.0.1:%s" % FLAGS.coordinator_port
    config["platform"] = FLAGS.platform
    config["task_config_entry"] = _gen_task_entry_config(client_root_dir, index)
    config["datasets"] = _gen_datasets_config(client_root_dir)

    # write new setup config
    with open(os.path.join(client_root_dir,
                           "%s.json" % FLAGS.job_name), "w") as f:
        json.dump(config, f)


def _gen_client_workspace(client_root_dir):
    workspace = os.path.join(client_root_dir, "workspace")
    _create_dir(workspace)

    return workspace


def _get_dataset_info():
    with open(os.path.join(
            current_dir,
            "example/jobs/%s/dataset_info.json" % FLAGS.job_name)) as f:
        dataset_info = json.load(f)

    return (dataset_info["train"], dataset_info["evaluate"],
            dataset_info["class_count"])


def _gen_task_entry_config(client_root_dir, client_index):
    entry_dir = os.path.join(client_root_dir, "task_entrys")
    _create_dir(entry_dir)

    with open(os.path.join(
            current_dir,
            "example/jobs/%s/%s.json" % (FLAGS.job_name, FLAGS.job_name))) as f:
        template_config = json.load(f)

    if FLAGS.data_split == "index":
        _split_data_with_index(template_config, client_index)
    elif FLAGS.data_split == "class":
        _split_data_with_class(template_config, client_index)
    elif FLAGS.data_split == "drichlet":
        _split_data_with_drichlet(template_config, client_index)
    else:
        logging.warning("Not support data_split with %s, the support is index"
                        "/class/drichlet", FLAGS.data_split)

    script_dir = os.path.join(entry_dir, FLAGS.job_name)
    template_config["script_path"] = script_dir
    _create_dir(script_dir)

    with open(os.path.join(entry_dir, "%s.json" % FLAGS.job_name), "w") as f:
        json.dump(template_config, f)

    return entry_dir


def _split_data_with_index(template_config, client_index):
    client_nums = len(FLAGS.client_ports.split(","))
    train_size, test_size, _ = _get_dataset_info()

    train_index_interval = int(train_size / client_nums)
    test_index_interval = int(test_size / client_nums)

    params = {"--index_range": "%s,%s" % (
        train_index_interval * client_index,
        train_index_interval * (client_index+1))}
    template_config["train"]["params"] = params
    params = {"--index_range": "%s,%s" % (
        test_index_interval * client_index,
        test_index_interval * (client_index + 1))}
    template_config["evaluate"]["params"] = params


def _split_data_with_class(template_config, client_index):
    client_nums = len(FLAGS.client_ports.split(","))
    _, _, class_count = _get_dataset_info()

    used_classes = []
    for class_num in range(class_count):
        if class_num % client_nums == client_index:
            used_classes.append(str(class_num))

    used_classes_str = ",".join(used_classes)
    params = {"--class_num": "%s" % used_classes_str}
    template_config["train"]["params"] = params
    params = {"--class_num": "%s" % used_classes_str}
    template_config["evaluate"]["params"] = params


def _split_data_with_drichlet(template_config, client_index):
    n_client = len(FLAGS.client_ports.split(","))
    saved_path, _, _, _, _ = gen_drichlet_distribution_data(
        FLAGS.dataset, FLAGS.dataset_name, n_client, FLAGS.drichlet_seed,
        FLAGS.drichlet_arg)
    params = {"--client_index": str(client_index),
              "--data_path": saved_path}
    template_config["train"]["params"] = params
    template_config["evaluate"]["params"] = params


def _gen_datasets_config(client_root_dir):
    datasets_config_path = os.path.join(client_root_dir, "datasets.json")

    datasets = {}
    if os.path.exists(datasets_config_path):
        with open(datasets_config_path) as f:
            previous_datasets = json.load(f)
            datasets.update(previous_datasets)

    with open(datasets_config_path, "w") as f:
        if FLAGS.dataset:
            datasets[FLAGS.job_name] = FLAGS.dataset

        json.dump(datasets, f)

    return datasets_config_path


def _gen_scripts(client_root_dir):
    _gen_train_script(client_root_dir)
    _gen_eval_script(client_root_dir)


def _gen_train_script(client_root_dir):
    script_dir = os.path.join(client_root_dir, "task_entrys", FLAGS.job_name)
    copyfile(os.path.join(current_dir,
                          "example/jobs/%s/train.py" % FLAGS.job_name),
             os.path.join(script_dir, "train.py"))


def _gen_eval_script(client_root_dir):
    script_dir = os.path.join(client_root_dir, "task_entrys", FLAGS.job_name)
    copyfile(os.path.join(current_dir,
                          "example/jobs/%s/evaluate.py" % FLAGS.job_name),
             os.path.join(script_dir, "evaluate.py"))


def _create_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def main(argv):
    """
    Main entry
    """
    del argv

    _create_dir(FLAGS.workspace)
    _gen_coordinator_setup_config()
    _gen_clients_config()


if __name__ == "__main__":
    app.run(main)
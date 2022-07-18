# -*- coding: utf-8 -*-
"""
"""
import json
import os
import sys
import yaml

from absl import app
from absl import flags
from absl import logging
from absl.logging import PythonFormatter


flags.DEFINE_enum("type", "server", ["server", "client"],
                  "Indicates whether the generated deployment files are "
                  "used to deploy server-side components or client-side "
                  "components.")
flags.DEFINE_string("config_file", None,
                    "Configuration file path which used to generate yaml files "
                    "or startup configuration files for deploying Neursafe-FL "
                    "components on K8S.")
flags.DEFINE_string("output", None,
                    "Path to save the generated deployment files.")


FLAGS = flags.FLAGS
FORMAT = ("[%(asctime)s] %(filename)s"
          "[line:%(lineno)d] %(levelname)s: %(message)s")
TEMPLATE_PATH = "./deploy/kubernetes/template"


def _set_log():
    class _Formatter(PythonFormatter):
        def format(self, record):
            return super(PythonFormatter,
                         self).format(record)

    logging.get_absl_handler().setFormatter(_Formatter(fmt=FORMAT))

    logging.set_verbosity("info")


def _load_config(config_file):
    with open(config_file) as f:
        try:
            configs = json.load(f)
        except json.decoder.JSONDecodeError:
            logging.error("Config file is not in json format.")
            sys.exit(1)

    return configs


def _load_yaml_template(path_):
    with open(path_) as f:
        tmp = yaml.safe_load_all(f.read())

    return next(tmp)


def _load_service_template():
    yaml_path = os.path.join(TEMPLATE_PATH, "service.yaml")
    return _load_yaml_template(yaml_path)


def _load_deployment_template():
    yaml_path = os.path.join(TEMPLATE_PATH, "deployment.yaml")
    return _load_yaml_template(yaml_path)


def _save_yaml(config, output, file_name):
    path_ = os.path.join(output, file_name)
    with open(path_, "w") as f:
        yaml.safe_dump_all(config, f)


def _gen_service_yaml(name, ports, namespace, external=False):
    service = _load_service_template()
    ports_ = []

    service["metadata"]["labels"]["app"] = name
    service["metadata"]["name"] = name
    service["metadata"]["namespace"] = namespace
    service["spec"]["selector"]["app"] = name

    if external:
        service["spec"]["type"] = "NodePort"

    for i, port in enumerate(ports):
        if external:
            ports_.append({"name": "port-%s" % i,
                           "port": port,
                           "targetPort": port,
                           "nodePort": port})
        else:
            ports_.append({"name": "port-%s" % i,
                           "port": port,
                           "targetPort": port})

    service["spec"]["ports"] = ports_

    return service


def _gen_deployment_yaml(name, ports, image, envs, volumes,
                         namespace, cmds=None):
    deployment = _load_deployment_template()
    ports_ = []
    volumes_ = []
    mounts = []

    deployment["metadata"]["labels"]["app"] = name
    deployment["metadata"]["name"] = name
    deployment["metadata"]["namespace"] = namespace
    deployment["spec"]["selector"]["matchLabels"]["app"] = name
    deployment["spec"]["template"]["metadata"]["labels"]["app"] = name

    container = deployment["spec"]["template"]["spec"]["containers"][0]
    container["image"] = image
    container["name"] = name
    container["env"] = envs

    if cmds:
        container["command"] = cmds

    for port in ports:
        ports_.append({"containerPort": port})
    container["ports"] = ports_

    for volume in volumes:
        mounts.append({"mountPath": volume["pod"], "name": volume["name"]})
        volumes_.append({"name": volume["name"],
                         "hostPath": {"path": volume["host"]}})
    container["volumeMounts"] = mounts

    deployment["spec"]["template"]["spec"]["volumes"] = volumes_

    return deployment


def _gen_optional_envs(options):
    envs = []

    for env_name, env_value in options.items():
        envs.append({"name": env_name,
                     "value": env_value})

    return envs


def _gen_model_manager_deployment_files(configs, output):
    name = configs["model_manager"]["service_name"]
    ports = [configs["model_manager"]["port"]]
    image = configs["model_manager"]["image"]
    namespace = configs["k8s"].get("namespace", "default")

    envs = [
        {"name": "STORAGE_ENDPOINT",
         "value": configs["storage"]["address"]},
        {"name": "STORAGE_TYPE",
         "value": configs["storage"]["type"]},
        {"name": "ACCESS_KEY",
         "valueFrom": {
             "secretKeyRef": {
                 "name": configs["storage"]["secret_key_ref"]["name"],
                 "key": configs["storage"]["secret_key_ref"]["user_key"]}}},
        {"name": "SECRET_KEY",
         "valueFrom": {
             "secretKeyRef": {
                 "name": configs["storage"]["secret_key_ref"]["name"],
                 "key": configs["storage"]["secret_key_ref"]["passwd_key"]}}
         },
        {"name": "DB_ADDRESS",
         "value": configs["db"]["address"]},
        {"name": "DB_USERNAME",
         "valueFrom": {
             "secretKeyRef": {
                 "name": configs["db"]["secret_key_ref"]["name"],
                 "key": configs["db"]["secret_key_ref"]["user_key"]}}},
        {"name": "DB_PASSWORD",
         "valueFrom": {
             "secretKeyRef": {
                 "name": configs["db"]["secret_key_ref"]["name"],
                 "key": configs["db"]["secret_key_ref"]["passwd_key"]}}
         },
        {"name": "DB_TYPE",
         "value": configs["db"]["type"]},
        {"name": "DB_NAME",
         "value": configs["db"]["name"]},
        {"name": "DB_COLLECTION_NAME",
         "value": configs["model_manager"]["db_collection_name"]},
        {"name": "PORT",
         "value": str(configs["model_manager"]["port"])},
        {"name": "LOG_LEVEL",
         "value": configs["others"]["log_level"]}]

    envs.extend(_gen_optional_envs(configs["model_manager"].get("options", {})))

    volumes = [{"name": "workspace",
                "pod": "/workspace",
                "host": configs["model_manager"][
                    "volumes"]["workspace"]["source"]}]

    service = _gen_service_yaml(name, ports, namespace)
    deployment = _gen_deployment_yaml(name, ports, image,
                                      envs, volumes, namespace)

    _save_yaml([service, deployment], output, "model-manager.yaml")


def _gen_job_scheduler_deployment_files(configs, output):
    name = configs["job_scheduler"]["service_name"]
    ports = [configs["job_scheduler"]["port"]]
    image = configs["job_scheduler"]["image"]
    namespace = configs["k8s"].get("namespace", "default")

    envs = [
        {"name": "DB_ADDRESS",
         "value": configs["db"]["address"]},
        {"name": "DB_USERNAME",
         "valueFrom": {
             "secretKeyRef": {
                 "name": configs["db"]["secret_key_ref"]["name"],
                 "key": configs["db"]["secret_key_ref"]["user_key"]}}},
        {"name": "DB_PASSWORD",
         "valueFrom": {
             "secretKeyRef": {
                 "name": configs["db"]["secret_key_ref"]["name"],
                 "key": configs["db"]["secret_key_ref"]["passwd_key"]}}
         },
        {"name": "DB_TYPE",
         "value": configs["db"]["type"]},
        {"name": "DB_NAME",
         "value": configs["db"]["name"]},
        {"name": "DB_COLLECTION_NAME",
         "value": configs["job_scheduler"]["db_collection_name"]},
        {"name": "HTTP_PORT",
         "value": str(configs["job_scheduler"]["port"])},
        {"name": "SELECTOR_ADDRESS",
         "value": "%s:%s" % (
             configs["client_selector"]["service_name"],
             configs["client_selector"]["port"])},
        {"name": "K8S_ADDRESS",
         "value": configs["k8s"]["address"]},
        {"name": "PROXY_ADDRESS",
         "value": "%s:%s" % (
             configs["proxy"]["service_name"],
             configs["proxy"]["http_port"])},
        {"name": "CLOUD_OS",
         "value": "k8s"},
        {"name": "COORDINATOR_IMAGE",
         "value": configs["coordinator"]["image"]},
        {"name": "JOB_SCHEDULER_ADDRESS",
         "value": "%s:%s" % (name, configs["job_scheduler"]["port"])},
        {"name": "TEMP_DIR",
         "value": configs["job_scheduler"]["coordinator_configs_dir"]},
        {"name": "WORKSPACE",
         "value": "/workspace"},
        {"name": "SOURCE_MOUNT_PATH",
         "value": configs[
             "job_scheduler"]["volumes"]["workspace"]["source"]},
        {"name": "GPU_RS_KEY",
         "value": configs["k8s"].get("gpu_rs_key", "nvidia.com/gpu")},
        {"name": "K8S_NAMESPACE",
         "value": configs["k8s"].get("namespace", "default")},
        {"name": "LOG_LEVEL",
         "value": configs["others"]["log_level"]}]

    envs.extend(_gen_optional_envs(configs["job_scheduler"].get("options", {})))

    volumes = [{"name": "workspace",
                "pod": "/workspace",
                "host": configs["job_scheduler"][
                    "volumes"]["workspace"]["source"]}]

    service = _gen_service_yaml(name, ports, namespace)
    deployment = _gen_deployment_yaml(name, ports, image, envs,
                                      volumes, namespace)

    _save_yaml([service, deployment], output, "job-scheduler.yaml")


def _gen_client_selector_deployment_files(configs, output):
    name = configs["client_selector"]["service_name"]
    ports = [configs["client_selector"]["port"]]
    image = configs["client_selector"]["image"]
    namespace = configs["k8s"].get("namespace", "default")

    envs = []
    envs.extend(_gen_optional_envs(
        configs["client_selector"].get("options", {})))

    volumes = [{"name": "config-file",
                "pod": "/nsfl/config/",
                "host": configs[
                    "client_selector"]["volumes"]["config"]["source"]}]

    cmds = ["python3.7", "-m", "neursafe_fl.python.selector.app",
            "--config_file", "/nsfl/config/client_selector_setup.json"]

    service = _gen_service_yaml(name, ports, namespace)
    deployment = _gen_deployment_yaml(name, ports, image, envs,
                                      volumes, namespace, cmds)

    _save_yaml([service, deployment], output, "client-selector.yaml")

    def _gen_client_selector_setup_file():
        with open(os.path.join(TEMPLATE_PATH,
                               "client_selector_setup.json")) as f:
            config = json.load(f)
            config["port"] = configs["client_selector"]["port"]
            config["log_level"] = configs["others"]["log_level"]

        with open(os.path.join(output,
                               "client_selector_setup.json"), "w") as f:
            json.dump(config, f)

    _gen_client_selector_setup_file()


def _gen_proxy_deployment_files(configs, output):
    name = configs["proxy"]["service_name"]
    namespace = configs["k8s"].get("namespace", "default")
    http_port = configs["proxy"]["http_port"]
    grpc_port = configs["proxy"]["grpc_port"]
    ports = [grpc_port, http_port]
    image = configs["proxy"]["image"]
    external = configs["proxy"]["external"]
    envs = []

    volumes = [{"name": "config-file",
                "pod": "/nginx/conf/",
                "host": configs[
                    "proxy"]["volumes"]["config"]["source"]}]

    service = _gen_service_yaml(name, ports, namespace, external)
    deployment = _gen_deployment_yaml(name, ports, image,
                                      envs, volumes, namespace)

    _save_yaml([service, deployment], output, "proxy.yaml")

    def _gen_nginx_conf():
        with open(os.path.join(TEMPLATE_PATH, "nginx.conf")) as f:
            config = f.read()
            config = config.replace("GRPC_PORT", str(grpc_port))
            config = config.replace("HTTP_PORT", str(http_port))
            config = config.replace("CLIENT_SELECTOR_SERVICE",
                                    configs["client_selector"]["service_name"])
            config = config.replace("CLIENT_SELECTOR_PORT",
                                    str(configs["client_selector"]["port"]))

        with open(os.path.join(output, "nginx.conf"), "w") as f:
            f.write(config)

    _gen_nginx_conf()


def _gen_api_server_deployment_files(configs, output):
    def gen_job_scheduler_ingress():
        with open(os.path.join(TEMPLATE_PATH,
                               "ingress-job-scheduler.yaml")) as f:
            config = f.read()
            config = config.replace("NAMESPACE",
                                    configs["k8s"].get("namespace", "default"))
            config = config.replace("JOB_SCHEDULER",
                                    configs["job_scheduler"]["service_name"])
            config = config.replace("PORT",
                                    str(configs["job_scheduler"]["port"]))

        with open(os.path.join(output, "ingress-job-scheduler.yaml"), "w") as f:
            f.write(config)

    def gen_model_manager_ingress():
        with open(os.path.join(TEMPLATE_PATH,
                               "ingress-model-manager.yaml")) as f:
            config = f.read()
            config = config.replace("NAMESPACE",
                                    configs["k8s"].get("namespace", "default"))
            config = config.replace("MODEL_MANAGER",
                                    configs["model_manager"]["service_name"])
            config = config.replace("PORT",
                                    str(configs["model_manager"]["port"]))

        with open(os.path.join(output, "ingress-model-manager.yaml"), "w") as f:
            f.write(config)

    def gen_nginx_ingress():
        with open(os.path.join(TEMPLATE_PATH,
                               "ingress-nginx.yaml")) as f:
            config = f.read()
            config = config.replace("HTTP_PORT",
                                    str(configs["api_server"]["http_port"]))
            config = config.replace("HTTPS_PORT",
                                    str(configs["api_server"]["https_port"]))

        with open(os.path.join(output, "ingress-nginx.yaml"), "w") as f:
            f.write(config)

    gen_job_scheduler_ingress()
    gen_model_manager_ingress()
    gen_nginx_ingress()


def _gen_task_manager_deployment_files(configs, output):
    name = configs["task_manager"]["service_name"]
    ports = [configs["task_manager"]["port"]]
    image = configs["task_manager"]["image"]
    external = configs["task_manager"]["external"]
    namespace = configs["k8s"].get("namespace", "default")

    envs = [
        {"name": "DB_ADDRESS",
         "value": configs["db"]["address"]},
        {"name": "DB_USERNAME",
         "valueFrom": {
             "secretKeyRef": {
                 "name": configs["db"]["secret_key_ref"]["name"],
                 "key": configs["db"]["secret_key_ref"]["user_key"]}}},
        {"name": "DB_PASSWORD",
         "valueFrom": {
             "secretKeyRef": {
                 "name": configs["db"]["secret_key_ref"]["name"],
                 "key": configs["db"]["secret_key_ref"]["passwd_key"]}}
         },
        {"name": "DB_TYPE",
         "value": configs["db"]["type"]},
        {"name": "DB_NAME",
         "value": configs["db"]["name"]},
        {"name": "DB_COLLECTION_NAME",
         "value": configs["task_manager"]["db_collection_name"]},
        {"name": "K8S_ADDRESS",
         "value": configs["k8s"]["address"]},
        {"name": "GPU_RS_KEY",
         "value": configs["k8s"].get("gpu_rs_key", "nvidia.com/gpu")},
        {"name": "K8S_NAMESPACE",
         "value": configs["k8s"].get("namespace", "default")},
        {"name": "CONTAINER_EXECUTOR_IMAGE",
         "value": configs["executor"]["image"]},
        {"name": "WORKER_PORT",
         "value": str(configs["executor"]["port"])},
        {"name": "WORKER_HTTP_PROXY",
         "value": configs["executor"]["http_proxy"]},
        {"name": "WORKER_HTTPS_PROXY",
         "value": configs["executor"]["https_proxy"]}]
    envs.extend(_gen_optional_envs(configs["task_manager"].get("options", {})))

    pod_mount_paths = {
        "lmdb": configs["task_manager"]["volumes"]["lmdb"]["source"],
        "workspace": configs["task_manager"]["volumes"]["workspace"]["source"],
        "datasets": configs["task_manager"]["volumes"]["datasets"]["source"],
        "task-configs": configs["task_manager"]["volumes"][
            "task-configs"]["source"],
        "config": configs["task_manager"]["volumes"]["config"]["source"]}

    volumes = []

    for name_, volume in configs["task_manager"]["volumes"].items():
        volumes.append({"name": name_,
                        "pod": pod_mount_paths[name_],
                        "host": volume["source"]
                        })

    cmds = ["python3.7", "-m", "neursafe_fl.python.client.app",
            "--config_file", os.path.join(pod_mount_paths["config"],
                                          "task_manager_setup.json")]

    service = _gen_service_yaml(name, ports, namespace, external)
    deployment = _gen_deployment_yaml(name, ports, image, envs,
                                      volumes, namespace, cmds)
    _save_yaml([service, deployment], output, "task-manager.yaml")

    def _gen_task_manager_setup_file():
        with open(os.path.join(TEMPLATE_PATH, "task_manager_setup.json")) as f:
            config = json.load(f)
            config["lmdb_path"] = pod_mount_paths["lmdb"]
            config["workspace"] = pod_mount_paths["workspace"]
            config["server"] = configs["task_manager"]["server_address"]

            config["port"] = configs["task_manager"]["port"]
            config["runtime"] = configs["task_manager"]["runtime"]
            config["datasets"] = os.path.join(pod_mount_paths["datasets"],
                                              "datasets.json")
            config["log_level"] = configs["others"]["log_level"]
            config["platform"] = configs["task_manager"]["platform"]
            config["task_config_entry"] = pod_mount_paths["task-configs"]
            config["registration"] = configs["task_manager"]["registration"]
            config["storage_quota"] = configs["task_manager"]["storage_quota"]

        with open(os.path.join(output, "task_manager_setup.json"), "w") as f:
            json.dump(config, f)

    _gen_task_manager_setup_file()


def _gen_server_deployment_files(config_file, output):
    configs = _load_config(config_file)

    _gen_job_scheduler_deployment_files(configs, output)
    _gen_client_selector_deployment_files(configs, output)
    _gen_proxy_deployment_files(configs, output)
    _gen_api_server_deployment_files(configs, output)
    _gen_model_manager_deployment_files(configs, output)


def _gen_client_deployment_files(config_file, output):
    configs = _load_config(config_file)

    _gen_task_manager_deployment_files(configs, output)


def _gen_deployment_files(type_, config_file, output):
    if type_ == "server":
        _gen_server_deployment_files(config_file, output)
    else:
        _gen_client_deployment_files(config_file, output)


def main(argv):
    del argv

    _set_log()

    params = FLAGS.flag_values_dict()

    type_ = params["type"]
    config_file = params["config_file"]
    output = params["output"]

    if not os.path.exists(config_file):
        logging.error("Config file is not existing.")
        sys.exit(1)

    if not os.path.exists(output):
        os.makedirs(output)

    _gen_deployment_files(type_, config_file, output)


if __name__ == "__main__":
    app.run(main)

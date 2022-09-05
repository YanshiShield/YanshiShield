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
                         namespace, cmds=None, image_pull_secret=None,
                         privileged=False):
    deployment = _load_deployment_template()
    ports_ = []
    volumes_ = []
    mounts = []

    deployment["metadata"]["labels"]["app"] = name
    deployment["metadata"]["name"] = name
    deployment["metadata"]["namespace"] = namespace
    deployment["spec"]["selector"]["matchLabels"]["app"] = name
    deployment["spec"]["template"]["metadata"]["labels"]["app"] = name

    if image_pull_secret:
        deployment["spec"]["template"]["spec"]["imagePullSecrets"] = [
            {"name": image_pull_secret}]

    container = deployment["spec"]["template"]["spec"]["containers"][0]
    container["image"] = image
    container["name"] = name
    container["env"] = envs

    if privileged:
        container["securityContext"] = {"privileged": True}

    if cmds:
        container["command"] = cmds

    for port in ports:
        ports_.append({"containerPort": port})
    container["ports"] = ports_

    for volume in volumes:
        mounts.append({"mountPath": volume["pod"], "name": volume["name"]})
        if volume["type"] == "pvc":
            volumes_.append({"name": volume["name"],
                             'persistentVolumeClaim': {
                                 'claimName': volume["pvc"]}})
        else:
            volumes_.append({"name": volume["name"],
                             'hostPath': {
                                 'path': volume["path"]}})
    container["volumeMounts"] = mounts

    deployment["spec"]["template"]["spec"]["volumes"] = volumes_

    return deployment


def _gen_optional_envs(options):
    envs = []

    for env_name, env_value in options.items():
        envs.append({"name": env_name,
                     "value": env_value})

    return envs


def _gen_storage_configs(storage):
    if storage["backend"]["type"].lower() == "s3":
        storage_envs = [
            {"name": "STORAGE_TYPE",
             "value": storage["backend"]["type"]},
            {"name": "S3_ENDPOINT",
             "value": storage["backend"]["address"]},
            {"name": "S3_ACCESS_KEY",
             "valueFrom": {
                 "secretKeyRef": {
                     "name": storage["backend"]["secret_key_ref"]["name"],
                     "key": storage["backend"]["secret_key_ref"]["user_key"]}}
             },
            {"name": "S3_SECRET_KEY",
             "valueFrom": {
                 "secretKeyRef": {
                     "name": storage["backend"]["secret_key_ref"]["name"],
                     "key": storage["backend"]["secret_key_ref"]["passwd_key"]}}
             },
            {"name": "WORKSPACE_BUCKET",
             "value": storage["backend"]["bucket"]},
        ]
        volumes = [{"name": "devfuse",
                    "type": "host",
                    "pod": "/dev/fuse",
                    "path": "/dev/fuse"}]
        privileged = True
    else:
        storage_envs = [
            {"name": "STORAGE_TYPE",
             "value": storage["backend"]["type"]},
            {"name": "WORKSPACE_PVC",
             "value": storage["backend"]["pvc"]}]
        volumes = [{"type": "pvc",
                    "name": "workspace",
                    "pod": "/workspace",
                    "pvc": storage["backend"]["pvc"]}]
        privileged = False

    return storage_envs, volumes, privileged


def _gen_model_manager_deployment_files(configs, output):
    name = configs["model_manager"]["service_name"]
    ports = [configs["model_manager"]["port"]]
    image = configs["model_manager"]["image"]
    namespace = configs["k8s"].get("namespace", "default")
    image_pull_secret = configs["k8s"].get("image_pull_secret")

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
         "value": configs["model_manager"]["db_collection_name"]},
        {"name": "PORT",
         "value": str(configs["model_manager"]["port"])},
        {"name": "MODELS_DIR",
         "value": configs["storage"]["models_dir"]},
        {"name": "LOG_LEVEL",
         "value": configs["others"]["log_level"]}]

    storage_envs, volumes, privileged = _gen_storage_configs(configs["storage"])

    envs.extend(storage_envs)
    envs.extend(_gen_optional_envs(configs["model_manager"].get("options", {})))

    service = _gen_service_yaml(name, ports, namespace)
    deployment = _gen_deployment_yaml(name, ports, image,
                                      envs, volumes, namespace,
                                      image_pull_secret=image_pull_secret,
                                      privileged=privileged)

    _save_yaml([service, deployment], output, "model-manager.yaml")


def _gen_data_server_deployment_files(configs, output):
    name = configs["data_server"]["service_name"]
    ports = [configs["data_server"]["port"]]
    image = configs["data_server"]["image"]
    namespace = configs["k8s"].get("namespace", "default")
    image_pull_secret = configs["k8s"].get("image_pull_secret")
    external = configs["proxy"]["external"]

    envs = [
        {"name": "ACCESS_USER",
         "valueFrom": {
             "secretKeyRef": {
                 "name": configs["data_server"]["secret_key_ref"]["name"],
                 "key": configs["data_server"]["secret_key_ref"]["user_key"]}}},
        {"name": "ACCESS_PASSWORD",
         "valueFrom": {
             "secretKeyRef": {
                 "name": configs["data_server"]["secret_key_ref"]["name"],
                 "key": configs["data_server"]["secret_key_ref"]["passwd_key"]}}
         },
        {"name": "PORT",
         "value": str(configs["data_server"]["port"])},
        {"name": "LOG_LEVEL",
         "value": configs["others"]["log_level"]}]

    storage_envs, volumes, privileged = _gen_storage_configs(configs["storage"])

    envs.extend(storage_envs)
    envs.extend(_gen_optional_envs(configs["data_server"].get("options", {})))

    service = _gen_service_yaml(name, ports, namespace, external)
    deployment = _gen_deployment_yaml(name, ports, image,
                                      envs, volumes, namespace,
                                      image_pull_secret=image_pull_secret,
                                      privileged=privileged)

    _save_yaml([service, deployment], output, "data-server.yaml")


def _gen_job_scheduler_deployment_files(configs, output):
    name = configs["job_scheduler"]["service_name"]
    ports = [configs["job_scheduler"]["port"]]
    image = configs["job_scheduler"]["image"]
    namespace = configs["k8s"].get("namespace", "default")
    image_pull_secret = configs["k8s"].get("image_pull_secret")

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
        {"name": "K8S_API_PROTOCOL",
         "value": configs["k8s"]["api_protocol"]},
        {"name": "K8S_API_TOKEN",
         "value": configs["k8s"]["api_token"]},
        {"name": "K8S_IMAGE_PULL_SECRETS",
         "value": configs["k8s"]["image_pull_secret"]},
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
         "value": configs["storage"]["coordinator_configs_dir"]},
        {"name": "WORKSPACE",
         "value": "/workspace"},
        {"name": "GPU_RS_KEY",
         "value": configs["k8s"].get("gpu_rs_key", "nvidia.com/gpu")},
        {"name": "K8S_NAMESPACE",
         "value": configs["k8s"].get("namespace", "default")},
        {"name": "LOG_LEVEL",
         "value": configs["others"]["log_level"]},
        {"name": "MODEL_MANAGER_ADDRESS",
         "value": "%s:%s" % (
             configs["model_manager"]["service_name"],
             configs["model_manager"]["port"])}]

    storage_envs, volumes, privileged = _gen_storage_configs(configs["storage"])

    envs.extend(storage_envs)
    envs.extend(_gen_optional_envs(configs["job_scheduler"].get("options", {})))

    service = _gen_service_yaml(name, ports, namespace)
    deployment = _gen_deployment_yaml(name, ports, image, envs,
                                      volumes, namespace,
                                      image_pull_secret=image_pull_secret,
                                      privileged=privileged)

    _save_yaml([service, deployment], output, "job-scheduler.yaml")


def _gen_client_selector_deployment_files(configs, output):
    name = configs["client_selector"]["service_name"]
    ports = [configs["client_selector"]["port"]]
    image = configs["client_selector"]["image"]
    namespace = configs["k8s"].get("namespace", "default")
    image_pull_secret = configs["k8s"].get("image_pull_secret")

    storage_envs, volumes, privileged = _gen_storage_configs(configs["storage"])

    envs = []
    envs.extend(storage_envs)
    envs.extend(_gen_optional_envs(
        configs["client_selector"].get("options", {})))

    cmds = ["python3.7", "-m", "neursafe_fl.python.selector.app",
            "--config_file", "/workspace/%s/client_selector_setup.json" %
            configs["storage"]["selector_dir"]]

    service = _gen_service_yaml(name, ports, namespace)
    deployment = _gen_deployment_yaml(name, ports, image, envs,
                                      volumes, namespace, cmds,
                                      image_pull_secret=image_pull_secret,
                                      privileged=privileged)

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
    image_pull_secret = configs["k8s"].get("image_pull_secret")
    envs = []

    storage_envs, volumes, privileged = _gen_storage_configs(configs["storage"])

    envs.extend(storage_envs)

    conf_dir = os.path.join("/workspace",
                             configs["storage"]["proxy_dir"].lstrip("/"))
    cmds = ["/nginx/start_nginx.sh", "/workspace",
            os.path.join(conf_dir, "nginx.conf")]

    service = _gen_service_yaml(name, ports, namespace, external)
    deployment = _gen_deployment_yaml(name, ports, image,
                                      envs, volumes, namespace, cmds,
                                      image_pull_secret=image_pull_secret,
                                      privileged=privileged)

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
    image_pull_secret = configs["k8s"].get("image_pull_secret")
    workspace = "/workspace"

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
        {"name": "K8S_API_PROTOCOL",
         "value": configs["k8s"]["api_protocol"]},
        {"name": "K8S_API_TOKEN",
         "value": configs["k8s"]["api_token"]},
        {"name": "K8S_IMAGE_PULL_SECRETS",
         "value": configs["k8s"]["image_pull_secret"]},
        {"name": "GPU_RS_KEY",
         "value": configs["k8s"].get("gpu_rs_key", "nvidia.com/gpu")},
        {"name": "K8S_NAMESPACE",
         "value": configs["k8s"].get("namespace", "default")},
        {"name": "CONTAINER_EXECUTOR_IMAGE",
         "value": configs["executor"]["image"]},
        {"name": "WORKER_PORT",
         "value": str(configs["executor"]["port"])},
        {"name": "WORKSPACE",
         "value": workspace},
        {"name": "WORKER_HTTP_PROXY",
         "value": configs["executor"]["http_proxy"]},
        {"name": "WORKER_HTTPS_PROXY",
         "value": configs["executor"]["https_proxy"]},
        {"name": "PERSIST_TASK_RESOURCE_USAGE",
         "value": "true"}]

    storage_envs, volumes, privileged = _gen_storage_configs(configs["storage"])
    envs.extend(storage_envs)
    envs.extend(_gen_optional_envs(configs["task_manager"].get("options", {})))

    paths = {
        "lmdb": os.path.join(workspace,
                             configs["storage"]["lmdb_dir"].lstrip("/")),
        "workspace": os.path.join(
            workspace, configs["storage"]["workspace_dir"].lstrip("/")),
        "datasets": os.path.join(
            workspace, configs["storage"]["datasets_dir"].lstrip("/")),
        "task_configs": os.path.join(
            workspace, configs["storage"]["task_configs_dir"].lstrip("/")),
        "config": os.path.join(
            workspace,
            configs["storage"]["task_manager_config_dir"].lstrip("/"))}

    cmds = ["python3.7", "-m", "neursafe_fl.python.client.app",
            "--config_file", os.path.join(paths["config"],
                                          "task_manager_setup.json")]

    service = _gen_service_yaml(name, ports, namespace, external)
    deployment = _gen_deployment_yaml(name, ports, image, envs,
                                      volumes, namespace, cmds,
                                      image_pull_secret=image_pull_secret,
                                      privileged=privileged)
    _save_yaml([service, deployment], output, "task-manager.yaml")

    def _gen_task_manager_setup_file():
        with open(os.path.join(TEMPLATE_PATH, "task_manager_setup.json")) as f:
            config = json.load(f)

            config["lmdb_path"] = paths["lmdb"]
            config["workspace"] = paths["workspace"]
            config["server"] = configs["task_manager"]["server_address"]
            config["port"] = configs["task_manager"]["port"]
            config["runtime"] = configs["task_manager"]["runtime"]
            config["datasets"] = os.path.join(paths["datasets"],
                                              "datasets.json")
            config["log_level"] = configs["others"]["log_level"]
            config["platform"] = "k8s"
            config["task_config_entry"] = paths["task_configs"]
            config["registration"] = configs["task_manager"]["registration"]
            config["storage_quota"] = configs["task_manager"]["storage_quota"]
            config["external_address"] = "%s:%s" % (
                configs["task_manager"]["service_ip"],
                configs["task_manager"]["port"])

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
    _gen_data_server_deployment_files(configs, output)


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

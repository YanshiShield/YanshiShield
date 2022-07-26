#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=invalid-name, too-many-instance-attributes, broad-except
"""Client Reporter Module.
"""
import os
import uuid
import asyncio

from absl import logging
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import MD5
from Crypto import Random
from OpenSSL import crypto

from neursafe_fl.proto.message_pb2 import ClientInfo, Client, ClientState, \
    ClientRegister
from neursafe_fl.proto.client_service_grpc import ClientServiceStub
from neursafe_fl.python.utils.file_io import read_json_file
from neursafe_fl.python.trans.grpc_call import unary_call
from neursafe_fl.python.resource_manager.plat_form.platform import PlatFormType


REPORT_HEARTBEAT = int(os.getenv("REPORT_HEARTBEAT", "150"))


def parse_dataset(dataset_config):
    """Parse dataset that the client have.
    """
    data = {}
    datasets = read_json_file(dataset_config)
    for dataset_name in datasets:
        data[dataset_name] = 1  # should set dataset size, default 1
    return data


class ClientReporter:
    """Client reporter.

    This class report client detail information to the server periodically.
    """
    def __init__(self, config, task_manager):
        # static attributes
        self.os = config["platform"]
        self.type = self.__get_platform_type(config["platform"])
        self.id = self.__gen_client_id()
        self.address = config.get("external_address", "%s:%s" %
                                  (config["host"], config["port"]))

        self.runtime = config.get("runtime", "tensorflow")
        self.label = config.get("label", "")
        self.datasets = config["datasets"]

        # dynamic attributes
        self.resource = {}
        self.state = None
        self.tasks = []
        self.max_parallelism = config.get("max_task_parallelism", -1)
        self.cur_parallelism = 0
        self.status = {}

        # auth info
        self.__username = config.get("username")
        self.__password = config.get("password")
        self.__public_key = config.get("public_key")
        self.__private_key = config.get("private_key")
        self.__certificate = config.get("certificate")

        self.__server_address = config.get("server")
        self.__registration = config.get("registration", "true")
        self.__workspace = config["workspace"]
        self.__ssl = None
        self.__task_manager = task_manager
        self.__session_id = None
        self.__report_interval = REPORT_HEARTBEAT
        self.__timer = None

    def __get_platform_type(self, platform):
        type_map = {PlatFormType.STANDALONE: "single",
                    PlatFormType.K8S: "cluster"}
        return type_map[platform]

    def __gen_client_id(self):
        client_uuid = str(uuid.uuid1())[10:]
        return "%s-%s-%s" % (self.type, self.os, client_uuid)

    def __gen_client_info(self):
        self.__update_client()
        client = Client(id=self.id, type=self.type)
        client_info = ClientInfo(client=client, os=self.os,
                                 runtime=self.runtime,
                                 address=self.address,
                                 state=self.state,
                                 tasks=self.tasks,
                                 max_task_parallelism=self.max_parallelism,
                                 cur_task_parallelism=self.cur_parallelism,
                                 client_label=self.label,
                                 client_data=parse_dataset(self.datasets),
                                 client_resource=self.resource,
                                 client_status=self.status)
        return client_info

    def __update_client(self):
        self._update_resource()
        self._update_status()
        self._update_state()

    def _update_resource(self):
        """Read current resource state from resource manager.

        Client's resource, including cpu, gpu memory. if return {} means
        resource state will be private, won't report.
        """
        self.resource = self.__task_manager.get_resources()

    def _update_status(self):
        """Record current client detail status.

        Keep the interface to record the state of the client itself, such as
        client's network, battery, or other extender status. Can be used for
        future selection. (current not used)
        (State is the overall state of the client, usable or not.)
        """
        self.status = {}

    def _update_state(self):
        tasks = self.__task_manager.get_tasks()
        self.tasks = ",".join([task[0] for task in tasks.keys()])
        self.cur_parallelism = len(tasks.keys())

        if self.max_parallelism == -1:  # always available
            self.state = ClientState.Value("available")
        elif self.cur_parallelism == 0:
            self.state = ClientState.Value("idle")
        elif self.cur_parallelism < self.max_parallelism:
            self.state = ClientState.Value("available")
        elif self.cur_parallelism == self.max_parallelism:
            self.state = ClientState.Value("full")
        else:
            self.state = ClientState.Value("error")

    async def start(self):
        """Start client reporter, report after every interval.
        """
        if self.__registration.lower() == "false":
            logging.warning("The registration switch is off, the client will "
                            "not join the fl system.")
            return

        self.__task_manager.set_client_id(self.id)
        self.__load_certificates()
        await self.__register()

        # report client information regularly if register success.
        self.__timer = await asyncio.create_task(self.__report())

    def __load_certificates(self):
        if self.__certificate and os.path.exists(self.__certificate):
            cert_buff = open(self.__certificate, "rb").read()
            cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_buff)
            self.__certificate = cert
            logging.info("Load certificate success.")

        if self.__public_key and self.__private_key:
            public_key = open(self.__public_key).read()
            private_key = open(self.__private_key).read()
        else:
            public_key, private_key = self.__generate_key_pair()
        self.__private_key = private_key
        self.__public_key = public_key
        logging.info("Load key pairs success.")

    def __generate_key_pair(self):
        random_generator = Random.new().read
        rsa = RSA.generate(2048, random_generator)
        path = os.path.join("/tmp", ".fl_certs")
        if not os.path.exists(path):
            os.mkdir(path)

        private_pem = rsa.exportKey()
        with open(os.path.join(path, 'private_key.pem'), 'wb') as f:
            f.write(private_pem)
        public_pem = rsa.publickey().exportKey()
        with open(os.path.join(path, 'public_key.pem'), 'wb') as f:
            f.write(public_pem)
        return public_pem, private_pem

    async def __register(self):
        """Register the client to server.
        """
        register_info = ClientRegister(client_id=self.id,
                                       username=self.__username,
                                       password=self.__password,
                                       certificate=self.__certificate,
                                       public_key=self.__public_key)

        result = await unary_call(ClientServiceStub, "Register", register_info,
                                  self.__server_address, self.__ssl)
        if result.state == "success":
            logging.info("Register client success.")
        else:
            raise RuntimeError("Register client failed, %s" % result.reason)

    async def __report(self):
        """Report client information and current state to server.
        """
        client_info = self.__gen_client_info()
        signature = self.__sign_message(client_info.SerializeToString())
        grpc_meta = {"signature-bin": signature}
        if self.__session_id:
            grpc_meta["session-id"] = self.__session_id

        try:
            result = await unary_call(ClientServiceStub, "Report", client_info,
                                      self.__server_address, self.__ssl,
                                      grpc_meta)
            if result.state == "success":
                logging.info("Report client to server success.")
            else:
                logging.info("Report client to server failed %s", result.reason)
        except Exception as err:
            logging.warning("Report to server failed, %s", str(err))

        await asyncio.sleep(self.__report_interval)
        self.__timer = await asyncio.create_task(self.__report())

    async def quit(self):
        """Quit the federate system.
        """
        if self.__timer:
            self.__timer.cancel()
        client = Client(id=self.id, type=self.type)
        signature = self.__sign_message(client.SerializeToString())
        grpc_meta = {"signature-bin": signature}
        if self.__session_id:
            grpc_meta["session-id"] = self.__session_id

        await unary_call(ClientServiceStub, "Quit", client,
                         self.__server_address, self.__ssl, grpc_meta)
        logging.info("Quit the client success.")

    def __sign_message(self, message):
        # sign the message with private key.
        if isinstance(message, str):
            msg_h = MD5.new(message.encode('utf-8'))
        else:
            msg_h = MD5.new(message)
        private_key = RSA.importKey(self.__private_key)
        signer = PKCS1_v1_5.new(private_key)
        signature = signer.sign(msg_h)
        return signature

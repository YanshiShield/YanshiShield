#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint: disable = arguments-differ, abstract-method, broad-except
# pylint: disable = attribute-defined-outside-init
"""
http handlers for job scheduler
"""
import json
from absl import logging

from tornado.web import RequestHandler
from tornado import gen

from neursafe_fl.python.job_scheduler.util.validations import \
    validate_job_config, validate_heartbeat
from neursafe_fl.python.job_scheduler.util.errors import JobSchedulerError, \
    JobNotExist


SYSTEM_ERROR_MSG = "Server Internal Error."


class BaseRequestHandler(RequestHandler):
    """base request handler
       include common method for all http handlers
    """

    def write_result(self, code, result):
        """
        Write http response

        Args:
            code: http code.
            result: http response body
        """
        self.set_status(code)
        self.write(json.dumps(result))

    def write_success(self, code):
        """
        Write successful http response

        Args:
            code: http code.
        """
        result = {"state": "SUCCEEDED"}

        self.write_result(code, result)

    def write_error(self, code, error_reason):
        """
        Write error http response

        Args:
            code: http code.
            error_reason: error message.
        """
        result = {"state": "FAILED",
                  "reason": error_reason}

        self.write_result(code, result)


class JobsHandler(BaseRequestHandler):
    """
    Fl jobs handler
    """

    URL = r'/api/v1/namespaces/(.*)/jobs'

    def initialize(self, scheduler):
        """
        Initialize handler

        Args:
            job_scheduler: job scheduler instance which handle http request.
        """
        self.__job_scheduler = scheduler

    @gen.coroutine
    def post(self, namespace):
        """
        Create federated job

        Args:
            namespace: fl job belongs to which namespace
        """
        try:
            job_config = json.loads(self.request.body)
            logging.info("Receive job create request, job config: %s",
                         job_config)
            validate_job_config(job_config)
            yield self.__job_scheduler.create_job(namespace, job_config)
            self.write_success(201)
        except (ValueError, TypeError, JobSchedulerError) as error:
            logging.exception(str(error))
            self.write_error(403, str(error))
        except Exception as error:
            logging.exception(str(error))
            self.write_error(500, SYSTEM_ERROR_MSG)

    def get(self, namespace):
        """
        Get federated jobs of namespace

        Args:
            namespace: fl jobs belong to which namespace
        """
        try:
            jobs = self.__job_scheduler.get_jobs(namespace)
            results = {"jobs": jobs}
            self.write_result(200, results)
        except Exception as error:
            logging.exception(str(error))
            self.write_error(500, SYSTEM_ERROR_MSG)


class JobHandler(BaseRequestHandler):
    """
    Fl job handler
    """

    URL = r'/api/v1/namespaces/(.*)/jobs/([\w|\-]{0,100})'

    def initialize(self, scheduler):
        """
        Initialize handler

        Args:
            job_scheduler: job scheduler instance which handle http request.
        """
        self.__job_scheduler = scheduler

    @gen.coroutine
    def put(self, namespace, job_id):
        """
        Update federated job

        Args:
            namespace: fl job belongs to which namespace.
            job_id: job index.
        """
        try:
            job_config = json.loads(self.request.body)
            logging.info("Receive job update request, namespace: %s, job "
                         "config: %s", namespace, job_config)
            validate_job_config(job_config)
            yield self.__job_scheduler.update_job(namespace, job_id, job_config)
            self.write_success(200)
        except (ValueError, TypeError, JobSchedulerError) as error:
            logging.error(str(error))
            self.write_error(403, str(error))
        except Exception as error:
            logging.exception(str(error))
            self.write_error(500, SYSTEM_ERROR_MSG)

    def get(self, namespace, job_id):
        """
        Get federated job

        Args:
            namespace: fl job belongs to which namespace.
            job_id: job index.
        """
        try:
            job = self.__job_scheduler.get_job(namespace, job_id)
            self.write_result(200, job)
        except JobNotExist as error:
            logging.error(str(error))
            self.write_error(404, str(error))
        except Exception as error:
            logging.exception(str(error))
            self.write_error(500, SYSTEM_ERROR_MSG)

    def delete(self, namespace, job_id):
        """
        Delete federated job

        Args:
            namespace: fl job belongs to which namespace.
            job_id: job index.
        """
        try:
            self.__job_scheduler.delete_job(namespace, job_id)
            self.write_success(200)
        except JobSchedulerError as error:
            logging.error(str(error))
            self.write_error(403, str(error))
        except Exception as error:
            logging.exception(str(error))
            self.write_error(500, SYSTEM_ERROR_MSG)


class HeartBeatHandler(BaseRequestHandler):
    """
    Heart beat handler
    """

    URL = r'/api/v1/heartbeat'

    def initialize(self, scheduler):
        """
        Initialize handler

        Args:
            job_scheduler: job scheduler instance which handle http request.
        """
        self.__job_scheduler = scheduler

    @gen.coroutine
    def put(self):
        """
        Update heart beat info
        """
        try:
            heart_beat = json.loads(self.request.body)
            logging.info("Receive job heartbeat: %s",
                         heart_beat)
            validate_heartbeat(heart_beat)
            yield self.__job_scheduler.handle_heartbeat(heart_beat)
            self.write_success(200)
        except (ValueError, TypeError) as error:
            logging.error(str(error))
            self.write_error(403, str(error))
        except Exception as error:
            logging.exception(str(error))
            self.write_error(500, SYSTEM_ERROR_MSG)


class StartJobHandler(BaseRequestHandler):
    """Start fl job handler"""

    URL = r'/api/v1/namespaces/(.*)/jobs/([\w|\-]{0,100}):start'

    def initialize(self, scheduler):
        """
        Initialize handler

        Args:
            scheduler: job scheduler instance which handle http request.
        """
        self.__job_scheduler = scheduler

    @gen.coroutine
    def put(self, namespace, job_id):
        """
        Start federated job

        Args:
            namespace: fl job belongs to which namespace.
            job_id: job index.
        """
        try:
            logging.info("Receive job start request, namespace: %s, job "
                         "id: %s.", namespace, job_id)
            yield self.__job_scheduler.start_job(namespace, job_id)
            self.write_success(200)
        except JobSchedulerError as error:
            logging.error(str(error))
            self.write_error(403, str(error))
        except Exception as error:
            logging.exception(str(error))
            self.write_error(500, SYSTEM_ERROR_MSG)


class StopJobHandler(BaseRequestHandler):
    """Stop fl job handler"""

    URL = r'/api/v1/namespaces/(.*)/jobs/([\w|\-]{0,100}):stop'

    def initialize(self, scheduler):
        """
        Initialize handler

        Args:
            scheduler: job scheduler instance which handle http request.
        """
        self.__job_scheduler = scheduler

    @gen.coroutine
    def put(self, namespace, job_id):
        """
        stop federated job

        Args:
            namespace: fl job belongs to which namespace.
            job_id: job index.
        """
        try:
            logging.info("Receive job stop request, namespace: %s, job "
                         "id: %s.", namespace, job_id)
            yield self.__job_scheduler.stop_job(namespace, job_id)
            self.write_success(200)
        except JobSchedulerError as error:
            logging.error(str(error))
            self.write_error(403, str(error))
        except Exception as error:
            logging.exception(str(error))
            self.write_error(500, SYSTEM_ERROR_MSG)


class HealthHandler(BaseRequestHandler):
    """
    Health handler
    """

    URL = r'/api/v1/health'

    def get(self):
        """
        Return job scheduler whether ok.
        """
        try:
            self.write_result(200, "OK")
        except Exception as error:
            logging.exception(str(error))
            self.write_error(500, SYSTEM_ERROR_MSG)

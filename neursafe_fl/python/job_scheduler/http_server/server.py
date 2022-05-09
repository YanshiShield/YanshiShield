#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

"""
http server
"""

from absl import logging

import tornado.web

from neursafe_fl.python.job_scheduler.util.const import HTTP_PORT
import neursafe_fl.python.job_scheduler.http_server.handlers as handlers


class HttpServer:  # pylint: disable=too-few-public-methods
    """
    Http server for handling request of fl job.
    """

    def __init__(self, scheduler):
        """
        scheduler: fl job scheduler which manage whole life cycle of fl jobs.
        """
        self.__scheduler = scheduler

    def start(self):
        """
        start http server
        """

        app = tornado.web.Application([
            (handlers.HeartBeatHandler.URL,
             handlers.HeartBeatHandler, {"scheduler": self.__scheduler}),
            (handlers.HealthHandler.URL,
             handlers.HealthHandler),
            (handlers.JobsHandler.URL,
             handlers.JobsHandler, {"scheduler": self.__scheduler}),
            (handlers.JobHandler.URL,
             handlers.JobHandler, {"scheduler": self.__scheduler}),
            (handlers.StartJobHandler.URL,
             handlers.StartJobHandler, {"scheduler": self.__scheduler}),
            (handlers.StopJobHandler.URL,
             handlers.StopJobHandler, {"scheduler": self.__scheduler})
        ])
        app.listen(HTTP_PORT)
        logging.info("Http server start on port: %s." % HTTP_PORT)
        tornado.ioloop.IOLoop.current().start()

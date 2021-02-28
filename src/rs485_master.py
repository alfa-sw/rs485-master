# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=logging-format-interpolation
# pylint: disable=line-too-long
# pylint: disable=invalid-name
# pylint: disable=too-many-lines

import sys
import os
import time
import asyncio
import logging
import traceback

import tornado.web            # pylint: disable=import-error
import tornado.httpserver     # pylint: disable=import-error
import tornado.ioloop         # pylint: disable=import-error
import tornado.websocket      # pylint: disable=import-error
import tornado.options        # pylint: disable=import-error

HERE = os.path.dirname(os.path.abspath(__file__))

LISTEN_PORT = 8000
LISTEN_ADDRESS = '127.0.0.1'

APPLICATION_OPTIONS = dict(
    debug=True,
    autoreload=True,
    template_path=os.path.join(HERE, "..", "templates"),
    compiled_template_cache=False)

GLOBAL_APPLICATION_INSTANCE = None


def get_application_instance():

    global GLOBAL_APPLICATION_INSTANCE  # pylint: disable=global-statement

    if GLOBAL_APPLICATION_INSTANCE is None:
        GLOBAL_APPLICATION_INSTANCE = Application()

    return GLOBAL_APPLICATION_INSTANCE


class HttpHandler(tornado.web.RequestHandler):  # pylint: disable=too-few-public-methods

    def get(self):

        ctx = {
            "title": "rs485 master",
            "footer": "",
        }
        ret = self.render("index.html", **ctx)
        return ret


class WebsockHandler(tornado.websocket.WebSocketHandler):

    def initialize(self):

        a = get_application_instance()
        a.web_socket_channels.append(self)

        logging.info(f"n. of active web_socket_channels:{len(a.web_socket_channels)}")

        self.msg_counter = 0

    def open(self, *args, **kwargs):

        super().open(args, kwargs)
        logging.info(f"")

    def on_message(self, message):

        logging.info(f"message:{message}")
        self.msg_counter += 1
        answ = {
            'time': time.asctime(),
            'js': 'document.getElementById("answer_target").innerHTML="{} [{}] {}";'.format(
                self.msg_counter, time.asctime(), message),
        }

        self.write_message(answ)

    def on_close(self):

        logging.info(f"")
        a = get_application_instance()
        a.web_socket_channels.remove(self)


class rs485_Master:

    async def run(self):

        msg_ = """ TO BE IMPLEMENTED ..."""

        while True:

            await asyncio.sleep(1)
            logging.warning(msg_)


class Application:

    url_map = [
        (r"/", HttpHandler, {}),
        (r'/websocket', WebsockHandler, {}),
    ]

    web_socket_channels = []

    def start_tornado(self):

        logging.info("starting tornado webserver on {}:{}...".format(LISTEN_ADDRESS, LISTEN_PORT))

        app = tornado.web.Application(self.url_map, **APPLICATION_OPTIONS)
        app.listen(LISTEN_PORT, LISTEN_ADDRESS)
        tornado.platform.asyncio.AsyncIOMainLoop().install()

    def start_backend_task(self):

        logging.info("starting backend task...")

        _future = rs485_Master().run()
        asyncio.ensure_future(_future)

    def run(self):

        self.start_tornado()
        self.start_backend_task()

        asyncio.get_event_loop().run_forever()


def main():

    logging.basicConfig(
        stream=sys.stdout, level="INFO",
        format="[%(asctime)s]%(levelname)s %(funcName)s() %(filename)s:%(lineno)d %(message)s")

    a = get_application_instance()
    a.run()

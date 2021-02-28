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

import json

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
        self.RS485_instance = rs485_Master()

    def open(self, *args, **kwargs):

        super().open(args, kwargs)
        logging.info(f"")

    def on_message(self, message):

        logging.info(f"message:{message}")
        try:
            in_message = json.loads(message)
            logging.info(in_message)
            self.msg_counter += 1
            cmd_name = in_message["command_name"]
            cmd_args = in_message["arguments"]
            inst = get_application_instance().rs485_instance
            answ = {"answer_name": cmd_name, "answer_content": inst.process_command(cmd_name, cmd_args)}
            self.write_message(answ)
        except Exception as e:
            logging.info(f"failed to decode message ", e)
            


    def on_close(self):

        logging.info(f"")
        a = get_application_instance()
        a.web_socket_channels.remove(self)


class rs485_Master:
    def start_backend_task(self):

        logging.info("starting backend task...")

        _future = self.run()
        asyncio.ensure_future(_future)
        
    def __init__(self):
        logging.info("RS485_Master init ...")
        self.start_backend_task()


    def connect(self, arguments):
        return True

    def disconnect(self, arguments):
        return True

    def sendOnSerial(self, arguments):
        return True

    def process_command(self, command_name, arguments):
        commands_ = {
           "connect": rs485_Master.connect,
           "disconnect": rs485_Master.disconnect,
           "send_on_serial": rs485_Master.disconnect,
        }

        return commands_[command_name](self, arguments)


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



    def run(self):
        self.start_tornado()

        asyncio.get_event_loop().run_forever()


def main():

    logging.basicConfig(
        stream=sys.stdout, level="INFO",
        format="[%(asctime)s]%(levelname)s %(funcName)s() %(filename)s:%(lineno)d %(message)s")

    a = get_application_instance()
    a.run()


if __name__ == '__main__':
    main()
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
import aioserial
from datetime import datetime

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
        
        def callback(signal, content):
            now = datetime.now()
            answ = {
                "signal": signal,
                "content": content,
                "timestamp": now.strftime("%d/%m/%Y %H:%M:%S")
            }
            self.write_message(answ)
        
        self.RS485_instance.set_feedback_callback(callback)


    def open(self, *args, **kwargs):

        super().open(args, kwargs)
        logging.info(f"")

    def answer(self, answer_name, answer_content):
        answ = {
            "answer": answer_name,
            "content": answer_content
        }
        self.write_message(answ)


    def on_message(self, message):

        logging.info(f"message:{message}")
        try:
            in_message = json.loads(message)
            logging.info(in_message)
            self.msg_counter += 1
            cmd_name = in_message["command_name"]
            cmd_args = in_message["arguments"]
            self.answer(cmd_name, self.process_command(cmd_name, cmd_args))
            
        except Exception as e:
            logging.info(f"failed to decode message ", e)
            

    def on_close(self):
        logging.info(f"")
        self.RS485_instance.disconnect()
        
        a = get_application_instance()
        a.web_socket_channels.remove(self)

    def process_command(self, command_name, cmd_args):
        commands_ = {
           "connect": rs485_Master.connect,
           "disconnect": rs485_Master.disconnect,
           "send_on_serial": rs485_Master.send_on_serial,
        }
        inst = self.RS485_instance
        return commands_[command_name](inst, **cmd_args)


class rs485_Master:
    """ A class to communicate to a serial port using asyncio coroutines.
    
    After configuring serial parameters (using method connect)
    the class establish a connection to a serial port, then stays 
    listening either to serial port, routing bytes by means
    of a callback function, either to the requests from another class: 
    write data, disconnect and so on. We call it the "client class".
    During initialization _run() is executed as a new asyncio task
    and remains alive for the lifetime of the instance. During the
    execution the status attribute changes:
     
     START -> 'wait_init' -> 'connected' -> 'disconnected' -> END
    
    Every time the main task wants to communicate something to 
    the client class the method defined as send_feedback attribute
    is fired. This happens when:
     - the status changes;
     - a new bunch of data arrives from serial.
     
    A set of methods allows the task to evolve by means of
    asyncio syncronization primitives.
    
    Methods
    -------
    connect(device_name=string, device_baudrate=int)
        Define serial connection parameters
        Returns True if the request is successful
        but client should check the status value to change too.

    disconnect()
        Disconnect and let the task die.
        Return boolean.

    send_on_serial(text=string)
        Send a line of text to serial.
        Return boolean.
    
    set_feedback_callback(function)
        Set the feedback callback function. It shall have
        two arguments: 
        - signal: the name of signal, e.g. 'recv_from_serial'
        - content: the attached data, e.g. the received text
        
    """
          
    def __init__(self):
        logging.info("RS485_Master init ...")
        
        self._connect_parameters = asyncio.Queue(maxsize=1)
        
        self._disconnect_event = asyncio.Event()
        self._write_queue = asyncio.Queue()
        self._set_status('wait_init')
        
        self._start_backend_task()

    def __del__(self):
        self.disconnect()

    def _start_backend_task(self):

        logging.info("starting backend task...")

        _future = self._run()
        asyncio.ensure_future(_future)

    def connect(self, *args, **kwargs):
        if self._current_status != 'wait_init':
            return False
        
        self._connect_parameters.put_nowait(kwargs)
        return True

    def disconnect(self, *args, **kwargs):
        if self._current_status != 'connected':
            return False
            
        self._disconnect_event.set()
        return True

    def send_on_serial(self, *args, **kwargs):
        self._write_queue.put_nowait(kwargs['text'])
        return True
        
    def set_feedback_callback(self, fct):
        self._send_feedback = fct

    def _set_status(self, current):
        self._current_status = current
        logging.info("set status to " + current)
        try:
            self._send_feedback('status', current)
        except:
            logging.info("unable to send feedback")
            
    async def _run(self):
        conn_params = await self._connect_parameters.get()
        
        serial = aioserial.AioSerial(
          port = conn_params['device_name'],
          baudrate = 9600)
        
        self._set_status('connected')
        
        async def read():
            logging.info("starting read")
            while True:
                text = await serial.read_until_async(aioserial.LF)
                logging.info("Recv text:" + text.decode("utf-8"))
                self._send_feedback('recv_from_serial', text.decode("utf-8"))

        async def write():
            while True:
                text = await self._write_queue.get()
                logging.info("Send text:" + text)
                await serial.write_async(text.encode('utf-8') + b'\n')
                
        read_task = asyncio.ensure_future(read())
        write_task = asyncio.ensure_future(write())

        await self._disconnect_event.wait()
        serial.close()
        self._set_status('disconnected')
        
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
import logging
import traceback

import abc
import sys

import asyncio
import aiofiles

from enum import Enum, auto

class Event(object):
    pass

class Observable(object):
    def __init__(self):
        self.callbacks = []
        
    def subscribe(self, callback):
        self.callbacks.append(callback)
        
    def fire(self, event, **attrs):
        e = Event()
        e.source = self
        e.event = event
        e.attachment = attrs
        for k, v in attrs.items():
            setattr(e, k, v)
        for fn in self.callbacks:
            fn(e)

class AbstractDriver(abc.ABC, Observable):
    class State(Enum):
        CONNECTED = auto()
        DISCONNECTED = auto()

    class Event(Enum):
        PACKET_RECV = auto()
        STATE_CHANGED = auto()
        
    def __init__(self):
        logging.info(f"Abstract Driver init")
        self.state = AbstractDriver.State.DISCONNECTED
        Observable.__init__(self)

    @abc.abstractmethod
    def __del__(self):
        """ Implement me! """
        pass

    @abc.abstractmethod
    def connect(self, **connection_parameters):
        """ Implement me! """
        pass

    @abc.abstractmethod
    def disconnect(self):
        """ Implement me! """
        pass

    @abc.abstractmethod
    def write(self, text):
        """ Implement me! """
        pass

    def get_current_status(self):
        return self.status

    def _set_current_status(self, state):
        self.state = state
        self.fire(AbstractDriver.Event.STATE_CHANGED, state = state)
        
class FileDriver(AbstractDriver):      
    def __init__(self):
        logging.info("RS485_Master init ...")
        self._disconnect_event = asyncio.Event()
        self._write_queue = asyncio.Queue()

        super().__init__()
        
    def __del__(self):
        self.disconnect()

    def connect(self, **connection_parameters):
        try:
            self.params = connection_parameters
            asyncio.ensure_future(self._run())
            self._set_current_status(self.State.CONNECTED)
        except:
            logging.info("Error while connecting:", sys.exc_info()[0])
            raise
            
    def disconnect(self):
        logging.info("Disconnect--")
        try:
            self._disconnect_event.set()
            self._set_current_status(self.State.DISCONNECTED)
        except:
            logging.info("Error while disconnecting:", sys.exc_info()[0])
            raise
                       
    def write(self, text):
        self._write_queue.put_nowait(text.encode('utf-8') + b'\n')

    async def _run(self):
        logging.info("starting read")
        
        async def read_task():
            async with aiofiles.open(self.params["port_rx"], mode="rb", buffering=0) as f:
                try:
                    while True:
                        buffer = b''
                        b = b''
                        while b != b'\n':
                            buffer = buffer + b 
                            b = await f.read(1)
                        logging.info("Recv text:" + buffer.decode("utf-8"))
                        self.fire(self.Event.PACKET_RECV, text = buffer.decode("utf-8"))
                except asyncio.CancelledError:
                       logging.info('reading task cancelled')
                    
        async def write_task():
            async with aiofiles.open(self.params["port_tx"], mode="wb", buffering=0) as f:
                text = await self._write_queue.get()
                logging.info("Send text:" + str(text))
                await f.write(text + b'\n')
            
        read_task = asyncio.ensure_future(read_task())
        write_task = asyncio.ensure_future(write_task())
        await self._disconnect_event.wait()
        read_task.cancel()
        write_task.cancel()
       

    
""" Implements low-level API to communication device.

Any class derived from AbstractDriver can be used 
from higher-level API to connect to the device and
make asyncronous read / write a packet, that is the array
of bytes between a starting and ending delimiter.

The class make use of the event handling system implemented
by class Observable. """

import logging
import traceback

import sys

import asyncio
import aiofiles
import abc

from enum import Enum, auto
from observable import Observable

class AbstractDriver(Observable):
    """ The virtual class implementing the abstract driver.
    Concrete drivers are derived from this class.
    There are two types of events that can be fired:
    - STATE_CHANGED: from CONNECTED (e['state']) to DISCONNECTED and viceversa
    - PACKET_RECV: a packet (e['text']) is received
    """
   
    DELIMITER_CODE =  b'\x03'

    class State(Enum):
        CONNECTED = auto()
        DISCONNECTED = auto()

    class EventLabel(Enum):
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
        """ Connect to device. If succeed the event STATE_CHANGED is fired.
        : param **connection_parameters: a dictionary with 
        the connection parameters. Please note that dict keys
        is expected to vary depending on the concrete class.
        """
        pass

    @abc.abstractmethod
    def disconnect(self):
        """ Disconnect to device. If succeed the event STATE_CHANGED is fired. """
        pass

    @abc.abstractmethod
    def write(self, text):
        """ Write a packet.
        : param text: a binary array to send, excluding the end delimiter.
        """
        pass

    def get_current_status(self):
        """ Get the current status. """
        return self.status

    def _set_current_status(self, state):
        self.state = state
        self.fire(AbstractDriver.EventLabel.STATE_CHANGED, state = state)
        
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
        logging.info("disconnecting")
        try:
            self._disconnect_event.set()
            self._set_current_status(self.State.DISCONNECTED)
        except:
            logging.info("Error while disconnecting:", sys.exc_info()[0])
            raise
                       
    def write(self, text):
        self._write_queue.put_nowait(bytes(text))

    async def _run(self):       
        async def read_task():
            logging.info("starting read")
            async with aiofiles.open(self.params["port_rx"], mode="rb", buffering=0) as f:
                try:
                    while True:
                        buffer = b''
                        b = b''
                        while b != self.DELIMITER_CODE:
                            b = await f.read(1)
                            if b == b'': # EOF reached
                               # sleep because after EOF read(1) starts to
                               # return immediately
                               await asyncio.sleep(0.1)
                            else:
                               buffer = buffer + b 
                               
                        logging.info("Recv text:" + buffer.decode("utf-8"))
                        self.fire(self.EventLabel.PACKET_RECV, text = buffer)
                except asyncio.CancelledError:
                       logging.info('reading task cancelled')
                    
        async def write_task():
            async with aiofiles.open(self.params["port_tx"], mode="wb", buffering=0) as f:
                text = await self._write_queue.get()
                logging.info("Send text:" + str(text))
                await f.write(text + self.DELIMITER_CODE)
            
        read_task = asyncio.ensure_future(read_task())
        write_task = asyncio.ensure_future(write_task())
        await self._disconnect_event.wait()
        read_task.cancel()
        write_task.cancel()
       

    
#!/usr/bin/env python3.8

from driver import FileDriver
import asyncio
import os
import unittest
import logging

class TestFileDriver(unittest.IsolatedAsyncioTestCase):
    fifo_in = '/tmp/fifo_test_in' 
    fifo_out = '/tmp/fifo_test_out'

    def setUp(self):
        os.mkfifo(self.fifo_in)
        os.mkfifo(self.fifo_out)
    
    def tearDown(self):
        os.remove(self.fifo_in)
        os.remove(self.fifo_out)

    async def test_file_driver(self):
        def observe_general(ev):
            print("Event: {k}, Attachment: {v} Source: {s}"
              .format(k = ev.label, v = ev.attachment, s = ev.source))

        def generate_observe_read():
            reads = []
            def observe_read(ev):
                if ev.label == FileDriver.EventLabel.PACKET_RECV:
                    reads.append(ev.attachment['text'])
            return (reads, observe_read)

        endpoint_A = FileDriver()
        endpoint_B = FileDriver()
        endpoint_A.subscribe(observe_general)
        endpoint_B.subscribe(observe_general)
        
        (reads, callback) = generate_observe_read()
        
        endpoint_B.subscribe(callback)
        
        endpoint_A.connect(port_rx = self.fifo_in, port_tx = self.fifo_out)
        endpoint_B.connect(port_rx = self.fifo_out, port_tx = self.fifo_in)
        
        endpoint_A.write(b"\x02test\x03")
        await asyncio.sleep(1)
        
        assert(len(reads) == 1)
        assert(reads[0] == b"\x02test\x03")

           
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()

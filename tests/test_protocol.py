#!/usr/bin/env python3

import os
import unittest
import logging
import asyncio

from driver import FileDriver
from protocol import Packer, Packet, Protocol
  
class TestPacker(unittest.TestCase):
    def test_encode_decode(self):
       src_addr = 0x20
       src_cmd_code = 0x09
       src_payload_bytes = b"\x10\x11\x12\x20\x21\x22"

       frame = Packer().encode_msg(Packet(src_addr, src_cmd_code, src_payload_bytes))
       packet = Packer().decode_msg(frame)
       ret_addr, ret_cmd_code, ret_payload_bytes = packet.get_as_tuple()
       assert(src_addr == ret_addr)
       assert(src_cmd_code == ret_cmd_code) 
       assert(src_payload_bytes == ret_payload_bytes)


class TestProtocol(unittest.IsolatedAsyncioTestCase):
    fifo_in = '/tmp/fifo_test_in' 
    fifo_out = '/tmp/fifo_test_out'

    def setUp(self):
        os.mkfifo(self.fifo_in)
        os.mkfifo(self.fifo_out)
    
    def tearDown(self):
        os.remove(self.fifo_in)
        os.remove(self.fifo_out)
 
    async def test_protocol(self):       
        def observe_general(ev):
            print("Event: {k}, Attachment: {v} Source: {s}"
              .format(k = ev.label, v = ev.attachment, s = ev.source))

        def generate_observe_read():
            packets = []
            def observe_read(ev):
                if ev.label == Protocol.EventLabel.PACKET_RECV:
                    packets.append(ev.attachment['packet'])
            return (packets, observe_read)


        endpoint_A = FileDriver()
        endpoint_B = FileDriver()
        endpoint_A.subscribe(observe_general)
        endpoint_B.subscribe(observe_general)
        
        proto_A = Protocol(endpoint_A)
        proto_B = Protocol(endpoint_B)
        
        proto_A.subscribe(observe_general)
        proto_B.subscribe(observe_general)
        (packets, callback) = generate_observe_read()       
        proto_B.subscribe(callback)
        
        endpoint_A.connect(port_rx = self.fifo_in, port_tx = self.fifo_out)
        endpoint_B.connect(port_rx = self.fifo_out, port_tx = self.fifo_in)

        src_addr = 0x20
        src_cmd_code = 0x09
        src_payload_bytes = b"\x10\x11\x12\x20\x21\x22"
        packet = Packet(src_addr, src_cmd_code, src_payload_bytes)
        proto_A.send_packet(packet)
        
        await asyncio.sleep(1)
        assert(len(packets) == 1)
        print(packets[0])
        
        assert(packets[0].addr == src_addr)
        assert(packets[0].cmd_code == src_cmd_code)
        assert(packets[0].payload_bytes == src_payload_bytes)
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()

#!/usr/bin/env python3.8

import os
import unittest
import logging

from protocol import MAB_MGB_protocol

class TestFileDriver(unittest.TestCase):
    def test_encode_decode(self):
       src_addr = 0x20
       src_cmd_code = 0x09
       src_payload_bytes = [0x10, 0x11, 0x12, 0x20, 0x21, 0x22]

       frame = MAB_MGB_protocol().encode_msg(src_addr, src_cmd_code, src_payload_bytes)
       ret_addr, ret_cmd_code, ret_payload_bytes = MAB_MGB_protocol().decode_msg(frame)
       assert(src_addr == ret_addr)
       assert(src_cmd_code == ret_cmd_code)       
       assert(src_payload_bytes == ret_payload_bytes)
           
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()

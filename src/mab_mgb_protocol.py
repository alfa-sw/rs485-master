# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=logging-format-interpolation
# pylint: disable=line-too-long
# pylint: disable=invalid-name
# pylint: disable=too-many-lines


class MAB_MGB_protocol:

    """ here we encapsulate the stuff related to the serial (low level) comm-protocol between MAB and MGB

        examples of encoded sequence of bytes (stuffed bytes, added the header, the crc, etc.):

        start(1) | addr(1) | len(1) | stuffed_payload(N) | crc(4) | end(1)

        where the first byte of the stuffed_payload is the command code

        << [0x02,0xE8,0x29,0x64,0x2F,0x27,0x29,0x2F,0x03]
        >> [0x02,0xE9,0x57,0xC8,0x07,0x01,0xFA,0xFB,0x01,0x1B,0x32,0x1B,0x33,0x04,0x05,0x06,0xFA,
                0xFB,0xFC,0xFD,0x01,0x01,0x01,0x01,0x00,0xFA,0xFB,0xFC,0xFD,0x05,0x04,0x1B,0x33,
                0x1B,0x32,0x00,0x00,0x21,0x53,0x05,0x06,0x01,0xFA,0xFB,0xFC,0xFD,0xFA,0xFB,0xFC,
                0xFD,0x26,0x25,0x2D,0x29,0x03]
    """

    # ~ /* reserved ASCII codes */
    ASCII_STX = 0x02
    ASCII_ETX = 0x03
    ASCII_ESC = 0x1B

    # ~ /* stuffying encodings */
    ASCII_ZERO = 0x30  # '0' /* ESC -> ESC ZERO  */
    ASCII_TWO = 0x32  # '2' /* STX -> ESC TWO   */
    ASCII_THREE = 0x33  # '3' /* ETX -> ESC THREE */

    MAB_ADDR = 200
    MGB_ADDR = 201

    CRC_TABLE = [
        0x0, 0x0C0C1, 0x0C181, 0x140, 0x0C301, 0x3C0, 0x280, 0x0C241,
        0x0C601, 0x6C0, 0x780, 0x0C741, 0x500, 0x0C5C1, 0x0C481, 0x440,
        0x0CC01, 0x0CC0, 0x0D80, 0x0CD41, 0x0F00, 0x0CFC1, 0x0CE81, 0x0E40,
        0x0A00, 0x0CAC1, 0x0CB81, 0x0B40, 0x0C901, 0x9C0, 0x880, 0x0C841,
        0x0D801, 0x18C0, 0x1980, 0x0D941, 0x1B00, 0x0DBC1, 0x0DA81, 0x1A40,
        0x1E00, 0x0DEC1, 0x0DF81, 0x1F40, 0x0DD01, 0x1DC0, 0x1C80, 0x0DC41,
        0x1400, 0x0D4C1, 0x0D581, 0x1540, 0x0D701, 0x17C0, 0x1680, 0x0D641,
        0x0D201, 0x12C0, 0x1380, 0x0D341, 0x1100, 0x0D1C1, 0x0D081, 0x1040,
        0x0F001, 0x30C0, 0x3180, 0x0F141, 0x3300, 0x0F3C1, 0x0F281, 0x3240,
        0x3600, 0x0F6C1, 0x0F781, 0x3740, 0x0F501, 0x35C0, 0x3480, 0x0F441,
        0x3C00, 0x0FCC1, 0x0FD81, 0x3D40, 0x0FF01, 0x3FC0, 0x3E80, 0x0FE41,
        0x0FA01, 0x3AC0, 0x3B80, 0x0FB41, 0x3900, 0x0F9C1, 0x0F881, 0x3840,
        0x2800, 0x0E8C1, 0x0E981, 0x2940, 0x0EB01, 0x2BC0, 0x2A80, 0x0EA41,
        0x0EE01, 0x2EC0, 0x2F80, 0x0EF41, 0x2D00, 0x0EDC1, 0x0EC81, 0x2C40,
        0x0E401, 0x24C0, 0x2580, 0x0E541, 0x2700, 0x0E7C1, 0x0E681, 0x2640,
        0x2200, 0x0E2C1, 0x0E381, 0x2340, 0x0E101, 0x21C0, 0x2080, 0x0E041,
        0x0A001, 0x60C0, 0x6180, 0x0A141, 0x6300, 0x0A3C1, 0x0A281, 0x6240,
        0x6600, 0x0A6C1, 0x0A781, 0x6740, 0x0A501, 0x65C0, 0x6480, 0x0A441,
        0x6C00, 0x0ACC1, 0x0AD81, 0x6D40, 0x0AF01, 0x6FC0, 0x6E80, 0x0AE41,
        0x0AA01, 0x6AC0, 0x6B80, 0x0AB41, 0x6900, 0x0A9C1, 0x0A881, 0x6840,
        0x7800, 0x0B8C1, 0x0B981, 0x7940, 0x0BB01, 0x7BC0, 0x7A80, 0x0BA41,
        0x0BE01, 0x7EC0, 0x7F80, 0x0BF41, 0x7D00, 0x0BDC1, 0x0BC81, 0x7C40,
        0x0B401, 0x74C0, 0x7580, 0x0B541, 0x7700, 0x0B7C1, 0x0B681, 0x7640,
        0x7200, 0x0B2C1, 0x0B381, 0x7340, 0x0B101, 0x71C0, 0x7080, 0x0B041,
        0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0, 0x5280, 0x9241,
        0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481, 0x5440,
        0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
        0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841,
        0x8801, 0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40,
        0x4E00, 0x8EC1, 0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41,
        0x4400, 0x84C1, 0x8581, 0x4540, 0x8701, 0x47C0, 0x4680, 0x8641,
        0x8201, 0x42C0, 0x4380, 0x8341, 0x4100, 0x81C1, 0x8081, 0x4040
    ]

    def __init__(self):

        pass

    def _crc16(self, data_bytes, CRCinit):

        index = 0x00
        for b in data_bytes:
            index = (CRCinit ^ (b & 0x00FF)) & 0x00FF
            CRCinit = ((CRCinit >> 8) & 0x00FF) ^ self.CRC_TABLE[index]

        return CRCinit

    def _unstuff_buffer(self, bytes_):
        " remove stuffing bytes where present."

        unstuffed_buff_list = []
        buff_list = list(bytes_)

        k = 0
        for i in range(len(buff_list)):
            if buff_list[k] == self.ASCII_ESC:
                if buff_list[k + 1] in (self.ASCII_TWO, self.ASCII_THREE):
                    unstuffed_buff_list.append(buff_list[k + 1] - self.ASCII_ZERO)
                elif buff_list[k + 1] in (self.ASCII_ZERO, ):
                    unstuffed_buff_list.append(self.ASCII_ESC)
                else:
                    raise ValueError('illegal sequence of bytes:{}'.format(bytes_))
                k = k + 1
            else:
                unstuffed_buff_list.append(buff_list[k])

            k = k + 1
            if k >= len(buff_list):
                break

        unstuffed_bytes = bytes(unstuffed_buff_list)

        return unstuffed_bytes

    def _stuff_buffer(self, bytes_):
        " add stuffing bytes where needed."

        stuffed_buff_list = []

        for byte_ in list(bytes_):
            # ~ /* STX --> ESC TWO, ETX --> ESC THREE */
            if byte_ in (self.ASCII_STX, self.ASCII_ETX):
                stuffed_buff_list.append(self.ASCII_ESC)
                stuffed_buff_list.append(byte_ + self.ASCII_ZERO)
            # ~ /* ESC --> ESC ZERO */
            elif byte_ == self.ASCII_ESC:
                stuffed_buff_list.append(self.ASCII_ESC)
                stuffed_buff_list.append(self.ASCII_ZERO)
            else:
                stuffed_buff_list.append(byte_)

        return bytes(stuffed_buff_list)

    def decode_msg(self, packet_bytes):
        """ takes in input a full sequence of bytes (as coming from serial port) coding for a full packet and
        returns: (addr, cmd_code, decoded_payload_bytes) """

        if packet_bytes[0] != self.ASCII_STX or packet_bytes[-1] != self.ASCII_ETX or len(packet_bytes) < 8:
            raise ValueError('illegal packet:{}'.format(" ".join(["0x%0X" % int(b) for b in packet_bytes])))

        addr = packet_bytes[1] - 0x20
        packet_len = packet_bytes[2] - 8 - 0x20
        stuffed_payload_bytes = packet_bytes[3:-5]
        crc_bytes = bytes(packet_bytes[0:-5])

        if len(stuffed_payload_bytes) != packet_len:
            raise ValueError('wrong packet length:{}/{} {}'.format(
                len(stuffed_payload_bytes), packet_len, " ".join(["0x%0X" % int(b) for b in packet_bytes])))

        payload_crc = self._crc16(crc_bytes, 0)
        decoded_payload_bytes = self._unstuff_buffer(stuffed_payload_bytes)

        pack_crc = 0
        pack_crc += ((packet_bytes[-5] - 0x20) << 12)
        pack_crc += ((packet_bytes[-4] - 0x20) << 8)
        pack_crc += ((packet_bytes[-3] - 0x20) << 4)
        pack_crc += ((packet_bytes[-2] - 0x20) << 0)

        if pack_crc != payload_crc:
            raise ValueError('wrong crc:0x{:04X}!=0x{:04X} {}'.format(
                pack_crc, payload_crc, ["0x%0X" % int(b) for b in packet_bytes[-5:-1]]))

        cmd_code = decoded_payload_bytes[0]
        _payload_bytes = decoded_payload_bytes[1:]

        return (addr, cmd_code, _payload_bytes)

    def encode_msg(self, addr, cmd_code, payload_bytes):
        """ takes in input (addr, cmd_code, payload_bytes_to_be_encoded)
        returns a full packet of bytes ready to be sent to serial port.  """

        payload_list = [cmd_code, ]
        payload_list += list(payload_bytes)

        ext_payload_bytes = bytes(payload_list)

        if len(ext_payload_bytes) > (256 - 20 - 8):
            raise ValueError("payload's length {} is out of range. payload:{}".format(
                len(ext_payload_bytes), ["0x%02X" % int(b) for b in ext_payload_bytes]))

        packet_list = []

        stuffed_payload_bytes = self._stuff_buffer(ext_payload_bytes)
        pack_len = len(stuffed_payload_bytes)

        packet_list += [self.ASCII_STX, ]
        packet_list += [addr + 0x20, ]
        packet_list += [pack_len + 8 + 0x20, ]
        packet_list += [stuffed_payload_bytes]

        pack_crc = self._crc16(bytes(packet_list), 0)
        # ~ in python2 function 'bytes()' is an alias for 'str()' so, has its idiosyncrasies
        pack_crc_0 = ((pack_crc >> 12) & 0x0F) + 0x20
        pack_crc_1 = ((pack_crc >> 8) & 0x0F) + 0x20
        pack_crc_2 = ((pack_crc >> 4) & 0x0F) + 0x20
        pack_crc_3 = ((pack_crc >> 0) & 0x0F) + 0x20

        packet_list += bytes([pack_crc_0, pack_crc_1, pack_crc_2, pack_crc_3, self.ASCII_ETX])

        packet_bytes = bytes(packet_list)

        return packet_bytes

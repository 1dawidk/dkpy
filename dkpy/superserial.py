import serial
import serial.tools.list_ports
import serial.serialutil
from typing import List


class SuperSerial:
    @staticmethod
    def find_serial(baudrate: int, tags: List[str], name: str = "uart device", encoding='utf-8', timeout=0.4):
        found_port = None

        print("Looking for {}...".format(name))
        ports = serial.tools.list_ports.comports()
        for port in ports:
            print('{}.'.format(port.device), end='', flush=True)
            ser = None

            try:
                ser = serial.Serial(port.device, baudrate, timeout=timeout)
                ser.flushInput()
                found_tag = False

                for i in range(5):
                    print('.', end='', flush=True)
                    l = ser.read(512)
                    ls = l.decode(encoding)

                    for t in tags:
                        if ls.find(t) > 0:
                            found_tag = True

                    if found_tag:
                        break

                ser.close()

                if found_tag:
                    print('  BINGO!')
                    found_port = port.device
                    break
                else:
                    print('  not in here :(')
            except serial.serialutil.SerialException:
                print('  Cannot open port! Skip!')
            except UnicodeDecodeError:
                print('  Cannot decode data! Wrong encoding!')
            finally:
                if (ser is not None) and ser.isOpen():
                    ser.close()

        return found_port

    @staticmethod
    def find_serial_with_poke(baudrate, poke: str, answer: str, name="uart device", encoding='utf-8', timeout=0.4):
        found_port = None

        print("Looking for {}...".format(name))
        ports = serial.tools.list_ports.comports()
        for port in ports:
            print('Poking {}.'.format(port.device), end='', flush=True)
            ser = None

            try:
                ser = serial.Serial(port.device, baudrate, timeout=timeout)
                ser.flushInput()
                ser.write(poke.encode())
                found_tag = False

                for i in range(5):
                    print('.', end='', flush=True)
                    l = ser.read(512)
                    ls = l.decode(encoding)

                    if ls.find(answer) >= 0:
                        found_tag = True
                        break

                ser.close()

                if found_tag:
                    print('  BINGO!')
                    found_port = port.device
                    break
                else:
                    print('  not in here :(')
            except serial.serialutil.SerialException:
                print('  Cannot open port! Skip!')
            except UnicodeDecodeError:
                print('  Cannot decode data! Wrong encoding!')
            finally:
                if (ser is not None) and ser.isOpen():
                    ser.close()

        return found_port


class SerialBuffer:
    def __init__(self, port, baudrate, maxlen=512, encoding='utf-8'):
        self.serial = serial.Serial(port, baudrate, timeout=0.05)
        self.buf = ''
        self.maxlen = maxlen
        self.encoding = encoding

    def update(self):
        if (self.serial is not None) and self.serial.is_open:
            buf_term = self.buf.find('\n')
            if buf_term > 0:
                ret = self.buf[:buf_term]
                if buf_term == (len(self.buf) - 1):
                    self.buf = ''
                else:
                    self.buf = self.buf[buf_term + 1:]

                return ret.strip("\r")
            elif buf_term == 0:
                self.buf = ''

            r = self.serial.readline().decode(encoding=self.encoding)
            term = r.find('\n')
            if term > 0:
                ret = self.buf + r[:term]
                if term == (len(r) - 1):
                    self.buf = ''
                else:
                    self.buf = r[term + 1:]

                return ret.strip("\r")
            else:
                self.buf += r
                print("No termination in readline()")
                return None
        else:
            print("Serial is not open")
            return None

    def close(self):
        self.serial.close()

    def is_open(self):
        return (self.serial is not None) and self.serial.is_open

    def write(self, msg):
        self.serial.write(bytes(msg, self.encoding))


class NMEAFormatError(Exception):
    pass


class NMEA:
    def __init__(self, msg: str = None, name: str = None, data=None):
        if msg is not None:
            msg = msg.strip('\n\r ')
            fs = msg.find(',')  # Find first separator
            terminator = len(msg) - 3

            if len(msg) < 4:
                raise NMEAFormatError('NMEA format corrupted! (Message too short)')
            elif msg[0] != '$':
                raise NMEAFormatError('NMEA format corrupted! ($ not found)')
            elif fs <= 0:
                raise NMEAFormatError('NMEA format corrupted! (First separator not found)')
            elif msg[terminator] != '*':
                raise NMEAFormatError('NMEA format corrupted! (Terminator not found)')
            else:
                if NMEA.checksum(msg) != msg[terminator + 1:].upper():
                    raise NMEAFormatError('Checksum invalid!')

                self.name = msg[1:fs]
                self.data = msg[fs + 1:-3].split(',')
                self.checksum = msg[-2:]
        elif (name is not None) and (data is not None):
            self.name = name
            self.data = data

            msg = name
            for d in data:
                msg += f',{d}'

            self.checksum = NMEA.checksum(msg)
        else:
            self.name = ""
            self.data = []
            self.checksum = "00"

    def data_len(self):
        return len(self.data)

    @staticmethod
    def checksum(msg: str):
        if msg[0] == '$':
            msg = msg[1:]

        terminator = msg.find('*')
        if terminator > 0:
            msg = msg[:terminator]

        chcksum = 0
        for ch in msg:
            chcksum = chcksum ^ ord(ch)

        return "{:02X}".format(chcksum)

    def __str__(self) -> str:
        msg = f'${self.name}'
        for d in self.data:
            msg += f',{d}'
        msg += f'*{self.checksum}\r\n'

        return msg

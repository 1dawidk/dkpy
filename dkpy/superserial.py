import serial
import serial.tools.list_ports


class SuperSerial:
    @staticmethod
    def find_serial(baudrate, tags, name="uart device"):
        found_port = None

        print("Looking for {}...".format(name))
        ports = serial.tools.list_ports.comports()
        for port in ports:
            print('{}.'.format(port.device), end='', flush=True)

            ser = serial.Serial(port.device, baudrate, timeout=0.5)
            ser.flushInput()
            found_tag = False

            for i in range(5):
                print('.', end='', flush=True)
                l = ser.read(254)
                ls = l.decode('utf-8')

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

        return found_port

    @staticmethod
    def find_serial_with_poke(baudrate, poke: str, answer: str, name="uart device"):
        found_port = None

        print("Looking for {}...".format(name))
        ports = serial.tools.list_ports.comports()
        for port in ports:
            print('Poking {}.'.format(port.device), end='', flush=True)

            ser = serial.Serial(port.device, baudrate, timeout=0.5)
            ser.flushInput()
            ser.write(poke.encode())
            found_tag = False

            for i in range(3):
                print('.', end='', flush=True)
                l = ser.read(512)
                ls = l.decode('utf-8')

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

        return found_port


class SerialBuffer:
    def __init__(self, port, baudrate, maxlen=512):
        self.serial = serial.Serial(port, baudrate, timeout=0.05)
        self.buf = ''
        self.maxlen = maxlen

    def update(self):
        if (self.serial is not None) and self.serial.is_open:
            r = self.serial.readline().decode()
            if r.find('\n') >= 0:
                ret = self.buf + r
                self.buf = ''
                return ret
            else:
                self.buf += r
                return ''
        else:
            return None

    def close(self):
        self.serial.close()

    def is_open(self):
        return (self.serial is not None) and self.serial.is_open


class NMEAFormatError(Exception):
    pass


class NMEA:
    def __init__(self, msg: str):
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

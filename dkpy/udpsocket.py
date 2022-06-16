import socket


class UDPSocket:
    BIND_FAILED = -1
    BIND_SUCCESS = 1

    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def start(self):
        try:
            self.soc.bind((self.ip, self.port))
            self.soc.setblocking(False)
        except OSError:
            return UDPSocket.BIND_FAILED

        return UDPSocket.BIND_SUCCESS

    def send(self, msg, ip, port):
        self.soc.sendto(msg.encode(), (ip, port))

    def send_bytes(self, bs, ip, port):
        self.soc.sendto(bs, (ip, port))

    def listen(self):
        try:
            data, addr = self.soc.recvfrom(1024)  # buffer size is 1024 bytes
            return addr, data.decode()
        except BlockingIOError:
            return None, None

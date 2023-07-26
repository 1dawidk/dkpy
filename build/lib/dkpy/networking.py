import subprocess
import time
import socket
import fcntl
import struct


class Networking:
    @staticmethod
    def is_intf_up(intf):
        res = subprocess.run(["cat", "/sys/class/net/" + intf + "/operstate"], stdout=subprocess.PIPE)
        return res.stdout.decode().find("up") >= 0

    @staticmethod
    def wait_intf_up(intf, max_time=30, verbose=True):
        start_at = time.time()
        while (not Networking.is_intf_up(intf)) and (time.time() - start_at < max_time):
            if verbose:
                print("Waitting for network is up...")
            time.sleep(1)

        return Networking.is_intf_up(intf)

    @staticmethod
    def get_intf_ip(intf):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', intf[:15])
        )[20:24])

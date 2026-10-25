"""VPS-side IPv4 UDP relay over one authenticated SSH channel.
Stdout is a binary framed protocol, never a log stream.
"""
import os
import select
import socket
import struct
import sys

MAX_FRAME=65513  # IPv4 address + port + maximum IPv4 UDP payload.
READY=b'NOVA_UDP_READY\n'


def write_all(fd,data):
    while data:
        count=os.write(fd,data)
        if count<=0:raise OSError('relay output closed')
        data=data[count:]


def main(port=19132):
    udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    udp.bind(('0.0.0.0',port))
    write_all(1,READY)
    buffer=bytearray()
    try:
        while True:
            readable,_,_=select.select([udp,0],[],[])
            if 0 in readable:
                data=os.read(0,65536)
                if not data:break
                buffer.extend(data)
                while len(buffer)>=4:
                    length=struct.unpack('!I',buffer[:4])[0]
                    if length<6 or length>MAX_FRAME:raise ValueError('invalid relay frame')
                    if len(buffer)<4+length:break
                    frame=bytes(buffer[4:4+length]);del buffer[:4+length]
                    address=(socket.inet_ntoa(frame[:4]),struct.unpack('!H',frame[4:6])[0])
                    udp.sendto(frame[6:],address)
            if udp in readable:
                data,address=udp.recvfrom(65507)
                frame=socket.inet_aton(address[0])+struct.pack('!H',address[1])+data
                write_all(1,struct.pack('!I',len(frame))+frame)
    finally:udp.close()

if __name__=='__main__':main(int(sys.argv[1]) if len(sys.argv)>1 else 19132)

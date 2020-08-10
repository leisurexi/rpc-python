# client

import json
import time
import struct
import socket


def rpc(sock, in_, params):
    # 请求消息体
    request = json.dumps({"in": in_, "params": params})
    # 请求长度前缀
    length_prefix = struct.pack("I", len(request))
    sock.sendall(length_prefix)
    sock.sendall(request.encode(encoding="utf-8", errors='strict'))
    # 响应长度前缀
    length_prefix = sock.recv(4)
    length, = struct.unpack("I", length_prefix)
    # 响应消息体
    body = sock.recv(length)
    response = json.loads(body.decode(encoding='utf-8', errors='strict'))
    # 返回响应类型和结果
    return response["out"], response["result"]


if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 8080))
    # 连续发送10个rpc请求
    for i in range(10):
        out, result = rpc(s, "ping", "ireader %d" % i)
        print(out, result)
        # 休眠1秒，便于观察
        time.sleep(1)
    s.close()

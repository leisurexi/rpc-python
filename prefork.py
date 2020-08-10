# prefork.py
# 进程要比现场更加吃资源，如果来一个连接就开一个进程，当连接比较多时，
# 进程数量也会跟着多起来，操作系统的调度压力也就会比较大。所以需要对
# 服务器开辟的进程数量进行限制，避免系统负载过重。
# 采用 PreForking 模型可以对子进程的数量进行了限制。PreForking
# 是通过预先产生多个子进程，共同对服务器套接字进行竞争性的 accept，
# 当一个连接到来时，每个子进程都有机会拿到这个连接，但是最终只会有
# 一个进程能 accept 成功返回拿到连接。子进程拿到连接后，进程内部
# 可以继续使用单线程或者多线程同步的形式对连接进行处理。

import os
import json
import struct
import socket


def handle_conn(conn, addr, handlers):
    print(addr, "comes")
    # 循环读写
    while True:
        # 请求长度前缀
        length_prefix = conn.recv(4)
        # 连接关闭了
        if not length_prefix:
            print(addr, "bye")
            conn.close()
            # 退出循环处理下一个连接
            break
        length, = struct.unpack("I", length_prefix)
        # 请求消息体
        body = conn.recv(length)
        request = json.loads(body.decode(encoding='utf-8', errors='strict'))
        in_ = request['in']
        params = request['params']
        print(in_, params)
        # 查找请求处理器
        handler = handlers[in_]
        # 处理请求
        handler(conn, params)


def loop(sock, handlers):
    while True:
        # 接收连接
        conn, addr = sock.accept()
        handle_conn(conn, addr, handlers)


def ping(conn, params):
    send_result(conn, "pong", params)


def send_result(conn, out, result):
    # 响应消息体
    response = json.dumps({"out": out, "result": result})
    # 响应长度前缀
    length_prefix = struct.pack("I", len(response))
    conn.sendall(length_prefix)
    conn.sendall(response.encode(encoding='utf-8', errors='strict'))


def prefork(n):
    for i in range(n):
        pid = os.fork()
        if pid < 0:
            return
        if pid > 0:
            continue
        if pid == 0:
            break


if __name__ == '__main__':
    # 创建一个 TCP 套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 打开 reuse addr 选项
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 绑定端口
    sock.bind(("localhost", 8080))
    # 监听客户端连接
    sock.listen(1)
    # 开启了10个子进程
    prefork(2)
    # 注册请求处理器
    handlers = {
        "ping": ping
    }
    # 进入服务循环
    loop(sock, handlers)

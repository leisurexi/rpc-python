# multiprocess.py
# Python 里多线程使用的并不常见，因为 Python 的 GIL 致使单个进程只能占满一个 CPU 核心，
# 多线程并不能充分利用多核的优势。所以多数 Python 服务器推荐使用多进程模型。我们将使用 Python 内置的 os.fork() 创建子进程

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
        # 创建子进程处理新连接
        pid = os.fork()
        if pid < 0:
            # 子进程创建失败，直接返回
            return
        if pid > 0:
            # 子进程创建成功，关闭父进程的客户端套接字引用，
            # 避免操作系统资源得不到释放导致资源泄露
            conn.close()
            continue
        if pid == 0:
            # 关闭子进程的服务器套接字引用
            sock.close()
            handle_conn(conn, addr, handlers)
            # 处理完后退出循环，不然子进程也会继续去 accept 连接
            break


def ping(conn, params):
    send_result(conn, "pong", params)


def send_result(conn, out, result):
    # 响应消息体
    response = json.dumps({"out": out, "result": result})
    # 响应长度前缀
    length_prefix = struct.pack("I", len(response))
    conn.sendall(length_prefix)
    conn.sendall(response.encode(encoding='utf-8', errors='strict'))


if __name__ == '__main__':
    # 创建一个 TCP 套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 打开 reuse addr 选项
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 绑定端口
    sock.bind(("localhost", 8080))
    # 监听客户端连接
    sock.listen(1)
    # 注册请求处理器
    handlers = {
        "ping": ping
    }
    # 进入服务循环
    loop(sock, handlers)

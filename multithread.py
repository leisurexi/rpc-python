# multithread.py
# 单线程同步模型服务器代码示例，每次只能处理一个客户端连接，
# 其它连接必须等到前面的连接关闭了才能得到服务器的处理。
# 否则发送过来的请求会悬挂住，没有任何响应，直到前面的连接处理完了才能继续

import json
import struct
import socket
import _thread


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
        # 开启新线程，处理连接
        _thread.start_new_thread(handle_conn, (conn, addr, handlers))


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

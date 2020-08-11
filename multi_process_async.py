# multi_process_async.py
# 多进程异步模型

import os
import json
import struct
import socket
import asyncore
from io import BytesIO


# 客户套接字处理器必须继承 dispatcher_with_send
class RPCHandler(asyncore.dispatcher_with_send):

    def __init__(self, sock, addr):
        asyncore.dispatcher_with_send.__init__(self, sock=sock)
        self.addr = addr
        self.handlers = {
            "ping": self.ping
        }
        # 读缓冲区由用户代码维护，写缓冲区由 asyncore 内部提供
        self.rbuf = BytesIO()

    # 新的连接被 accept 后回调方法
    def handle_connect(self):
        print(self.addr, 'comes')

    # 连接关闭之前回调方法
    def handle_close(self):
        print(self.addr, 'bye')
        self.close()

    # 有读事件到来时回调方法
    def handle_read(self):
        while True:
            content = self.recv(1024)
            if content:
                # 追加到读缓冲区
                self.rbuf.write(content)
            # 说明内核缓冲区空了，等待下个事件循环再继续读
            if len(content) < 1024:
                break
        # 处理新读到的消息
        self.handle_rpc()

    # 将读到的消息解包并处理
    def handle_rpc(self):
        # 可能一次性收到了多个请求消息，所以需要循环处理
        while True:
            self.rbuf.seek(0)
            length_prefix = self.rbuf.read(4)
            # 不足一个消息的长度，半包
            if len(length_prefix) < 4:
                break
            length, = struct.unpack("I", length_prefix)
            body = self.rbuf.read(length)
            # 还是半包
            if len(body) < length:
                break
            request = json.loads(body.decode(encoding="utf-8", errors='strict'))
            in_ = request['in']
            params = request['params']
            print(os.getpid(), in_, params)
            handler = self.handlers[in_]
            # 处理消息
            handler(params)
            # 消息处理完了，缓冲区要截断
            left = self.rbuf.getvalue()[length + 4:]
            self.rbuf = BytesIO()
            self.rbuf.write(left)
        # 将游标挪到文件末尾，以便后续读到的内容直接追加
        self.rbuf.seek(0, 2)

    def ping(self, params):
        self.send_result("pong", params)

    def send_result(self, out, result):
        response = {"out": out, "result": result}
        body = json.dumps(response)
        length_prefix = struct.pack("I", len(body))
        # 写入缓冲区
        self.send(length_prefix)
        # 写入缓冲区
        self.send(body.encode(encoding="utf-8", errors='strict'))


# 服务器套接字处理器必须继承 dispatcher
class RPCServer(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(1)
        # 开辟10个子进程
        self.prefork(10)

    def prefork(self, n):
        for i in range(n):
            pid = os.fork()
            if pid < 0:
                # fork error
                return
            if pid > 0:
                # parent process
                continue
            if pid == 0:
                # 子进程
                break

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            RPCHandler(sock, addr)


if __name__ == '__main__':
    RPCServer("localhost", 8080)
    asyncore.loop()

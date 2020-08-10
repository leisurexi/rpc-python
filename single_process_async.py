# single_process_async.py
# 单进程异步模型

import json
import struct
import socket
import asyncore
from io import StringIO

# 客户
# class RPCHandler(asyncore.dispatcher_with_send):
"""
    Code based on:
        https://github.com/mvillalba/python-ant/blob/develop/demos/ant.core/03-basicchannel.py
    in the python-ant repository and
        https://github.com/tomwardill/developerhealth
    by Tom Wardill
"""
import sys
import time
from datetime import datetime

import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado.ioloop import PeriodicCallback


from ant.core import driver, node, event, message, log
from ant.core.constants import CHANNEL_TYPE_TWOWAY_RECEIVE, TIMEOUT_NEVER

class HRM(event.EventCallback, tornado.web.RequestHandler):

    def __init__(self, serial, netkey):
        self.serial = serial
        self.netkey = netkey
        self.antnode = None
        self.channel = None

    def start(self):
        print("starting node")
        self._start_antnode()
        self._setup_channel()
        self.channel.registerCallback(self)
        print("start listening for hr events")

    def stop(self):
        if self.channel:
            self.channel.close()
            self.channel.unassign()
        if self.antnode:
            self.antnode.stop()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.stop()

    def _start_antnode(self):
        stick = driver.USB2Driver(self.serial)
        self.antnode = node.Node(stick)
        self.antnode.start()

    def _setup_channel(self):
        key = node.NetworkKey('N:ANT+', self.netkey)
        self.antnode.setNetworkKey(0, key)
        self.channel = self.antnode.getFreeChannel()
        self.channel.name = 'C:HRM'
        self.channel.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_RECEIVE)
        self.channel.setID(120, 0, 0)
        self.channel.setSearchTimeout(TIMEOUT_NEVER)
        self.channel.setPeriod(8070)
        self.channel.setFrequency(57)
        self.channel.open()

    def process(self, msg):
        if isinstance(msg, message.ChannelBroadcastDataMessage):
            # d = datetime.datetime.now().time()
            # print('%s:%s:%s.%s' % (d.hour, d.minute, d.second, d.microsecond))
            print("heart rate is {}".format(ord(msg.payload[-1])))

    def open(self):
        self.i = 0
        self.callback = PeriodicCallback(self._send_message, 400)  # 遅延用コールバック
        self.callback.start()
        print
        "WebSocket opened"

        # クライアントからメッセージが送られてくると呼び出される

    def on_message(self, message):
        print
        message

    # コールバックスタートで呼び出しが始まる
    def _send_message(self):
        self.i += 1
        self.write_message(str(self.i))

    # ページが閉じ、コネクションが切れる事で呼び出し
    def on_close(self):
        self.callback.stop()
        print
        "WebSocket closed"


SERIAL = '/dev/ttyUSB0'
NETKEY = 'B9A521FBBD72C345'.decode('hex')

with HRM(serial=SERIAL, netkey=NETKEY) as hrm:
    hrm.start()
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)
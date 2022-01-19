import threading
from time import sleep, time
from message import MSG_ACK, MSG_UND, MSG_TOK, MSG_REC, Message
from random import random

class Node:
    def __init__(self, rank, comm, node_count, success_rate = 1):
        self.rank = rank
        self.comm = comm
        self.success_rate = success_rate
        self.node_count = node_count
        self._has_token = False
        self._got_ack = None
        self._turn = 0
        self.sem = threading.Semaphore()
        self._init_receiver()

    def send(self, to, message, tag=0):
        if (self.success_rate > random()):
            print(f"{self.rank}) Send succesful", flush=True)
            self.comm.send(message, dest=to, tag=tag)
        else:
            print(f"{self.rank}) Send error", flush=True)

    def sure_send(self, to, message, tag=0, timeout=1):
        def _sure_send():
            got_ack = False
            while not got_ack:
                self.send(to, message, tag)
                sleep(timeout)
                with self.sem:
                    got_ack = self._got_ack
            with self.sem:
                self._got_ack = None
        sure_sender_thread = threading.Thread(target=_sure_send)
        sure_sender_thread.start()
        return sure_sender_thread

    def _init_receiver(self):
        def __receiver():
            while True:
                msg: Message = self.comm.recv()
                if msg.msg_type == MSG_UND:
                    print(f"{self.rank}) Received UND {msg}, sending ACK", flush=True)
                    res = Message(self.rank, msg.src, MSG_ACK, "OK", msg.turn)
                    self.send(msg.src, res)
                elif msg.msg_type == MSG_ACK:
                    print(f"{self.rank}) Received ACK {msg} setting got ACK", flush=True)
                    with self.sem:
                        self._got_ack = True
                elif msg.msg_type == MSG_TOK:
                    if msg.turn == self._turn:
                        self._turn = ((self._turn + 1) % 2)
                        self._has_token = True

                    res = Message(self.rank, msg.src, MSG_ACK, "OK", msg.turn)
                    self.send(msg.src, res)
                elif msg.msg_type == MSG_REC:
                    pass
                else:
                    print(f"{self.rank}) NYI {msg}", flush=True)
                # TODO: handle message receive
                pass
        receiver_thread = threading.Thread(target = __receiver)
        receiver_thread.start()

    def pass_token(self):
        if self._has_token:
            self.sure_send()
        else:
            pass

from sys import stderr
import threading
from time import sleep, time
from message import MSG_ACK, MSG_UND, MSG_TOK, MSG_REC, MSG_RCK, Message
from random import random

class Node:
    def __init__(self, rank, comm, node_count, success_rate=1, no_acks=False, deny_from=[]):
        self.rank = rank
        self.comm = comm
        self.success_rate = success_rate
        self.node_count = node_count
        self._has_token = False
        self._got_ack = None
        self._got_rec_ack = None
        self._turn = 0
        self._sending_recovery = False
        self.no_acks = False
        self.deny_from = deny_from
        self.sem = threading.Semaphore()
        self._init_receiver()

    def send(self, to, message: Message, tag=0):
        chance = random()
        if (self.no_acks and message.msg_type == MSG_ACK):
            print(f"{self.rank}) Send error (No ACKs)", flush=True)
        elif (self.success_rate >= chance):
            print(f"{self.rank}) Send succesful {message}", flush=True)
            self.comm.send(message, dest=to, tag=tag)
        elif (self.success_rate < chance):
            print(f"{self.rank}) Send error (Probability)", flush=True)

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
                if msg.src in self.deny_from:
                    print(f"{self.rank}) Receive Error (Deny from: {self.deny_from}) {msg}")
                    continue
                if msg.msg_type == MSG_UND:
                    print(f"{self.rank}) Received UND {msg}, sending ACK", flush=True)
                    res = Message(self.rank, msg.src, MSG_ACK, "OK", msg.turn)
                    self.send(msg.src, res)
                elif msg.msg_type == MSG_ACK:
                    print(f"{self.rank}) Received ACK {msg} setting got ACK", flush=True)
                    with self.sem:
                        self._got_ack = True
                elif msg.msg_type == MSG_RCK:
                    print(f"{self.rank}) Received RCK {msg} setting got REC ACK", flush=True)
                    if self._sending_recovery:
                        self._got_rec_ack = True
                elif msg.msg_type == MSG_TOK:
                    print(f"{self.rank}) Received TOK {msg}, sending ACK", flush=True)
                    if msg.turn == self._turn:
                        self._has_token = True
                        self._got_ack = True

                    res = Message(self.rank, msg.src, MSG_ACK, "OK", msg.turn)
                    self.send(msg.src, res)
                elif msg.msg_type == MSG_REC:
                    print(f"{self.rank}) Received REC {msg}, sending RCK", flush=True)
                    res = Message(self.rank, msg.src, MSG_RCK, "RECOK", msg.turn)
                    self.send(msg.src, res)
                    if msg.dest == self.rank:
                        if msg.turn == self._turn:
                            self._has_token = True
                        else:
                            pass
                    else:
                        if self._has_token:
                            pass
                        if not self._sending_recovery:
                            self._sending_recovery = True
                            next_receiver = -1
                            if self.rank < msg.src: # send to the left or send by the last one to first one
                                if self.rank == 0:
                                    next_receiver = self.node_count - 1 if ((self.rank - 1) < 0) else (self.rank - 1)
                                else:
                                    next_receiver = (self.rank + 1) % self.node_count
                            else: # send to to right or by the first one to the last one
                                if self.rank == self.node_count-1:
                                    next_receiver = (self.rank + 1) % self.node_count
                                else:
                                    next_receiver = self.node_count - 1 if ((self.rank - 1) < 0) else (self.rank - 1)
                            pass_recovery_thread = threading.Thread(target = self.pass_recovery_token, args=[next_receiver, msg.dest, msg.turn])
                            pass_recovery_thread.start()
                else:
                    print(f"{self.rank}) Received unknown message_type {msg}", flush=True)
        receiver_thread = threading.Thread(target = __receiver)
        receiver_thread.start()

    def enter_section(self):
        print(f"{self.rank}) Waiting for critical section...")
        while(not self._has_token):
            sleep(1)
        print(f"{self.rank}) Entering critical section")

    def leave_section(self):
        pass_token_thread = threading.Thread(target = self.pass_token)
        pass_token_thread.start()
        print(f"{self.rank}) Leaving critical section")

    def pass_recovery_token(self, receiver_no, msg_dest, msg_turn):
        while not self._got_rec_ack:
            self._sending_recovery = True
            if receiver_no == (self.rank + 1) % self.node_count:
                receiver_no = self.node_count - 1 if ((self.rank - 1) < 0) else (self.rank - 1)
            else:
                receiver_no = (self.rank + 1) % self.node_count

            msg = Message(self.rank, msg_dest, MSG_REC, "RECOVERY", msg_turn)
            self.send(receiver_no, msg)
            print(f"{self.rank}) No ACK after timeout, sending RECOVERY {msg} to {receiver_no}")
            sleep(2)
        self._sending_recovery = False
        self._got_rec_ack = None

    def pass_token(self):
        if self._has_token:
            self._has_token = False
            msg = Message(self.rank, (self.rank + 1) % self.node_count, MSG_TOK, "TOKEN", self._turn)
            receiver_no = (self.rank + 1) % self.node_count
            self.send(receiver_no, msg)
            sleep(2)

            got_ack = False
            with self.sem:
                got_ack = self._got_ack
            if not got_ack:
                pass_recovery_thread = threading.Thread(target = self.pass_recovery_token, args=[receiver_no, receiver_no, self._turn])
                pass_recovery_thread.start()
            else:
                with self.sem:
                    self._got_ack = False

            self._turn = ((self._turn + 1) % 2)
        else:
            print(f"{self._rank}) Doesn't have the token! (so he can't pass it)", file=stderr)

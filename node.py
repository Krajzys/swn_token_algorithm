from sys import stderr
import threading
from time import sleep, time
from message import MSG_ACK, MSG_TOK, MSG_REC, MSG_RCK, Message
from random import random
import logging

class Node:
    def __init__(self, rank, comm, node_count, success_rate=1, no_acks=False, deny_from=[], log_file=""):
        self.rank = rank
        self.comm = comm
        self.success_rate = success_rate
        self.node_count = node_count
        self._has_token = False
        self._got_ack = None
        self._got_rec_ack = None
        self._turn = 0
        self._sending_recovery = False
        self.no_acks = no_acks
        self.deny_from = deny_from
        if log_file != "":
            logging.basicConfig(filename=log_file, level=logging.INFO, format=f'{self.rank}:%(message)s')

        self.sem = threading.Semaphore()
        self._init_receiver()

    def send(self, to, message: Message, tag=0):
        chance = random()
        if (self.no_acks and message.msg_type == MSG_ACK):
            logging.log(logging.INFO, f"Send error (No ACKs)")
        elif (self.success_rate >= chance):
            logging.log(logging.INFO, f"Send succesful {message}")
            self.comm.send(message, dest=to, tag=tag)
        elif (self.success_rate < chance):
            logging.log(logging.INFO, f"Send error (Probability)")

    def _init_receiver(self):
        def __receiver():
            while True:
                msg: Message = self.comm.recv()
                if msg.src in self.deny_from:
                    logging.log(logging.INFO, f"Receive Error (Deny from: {self.deny_from}), MSG:{msg}")
                    continue
                elif msg.msg_type == MSG_ACK:
                    logging.log(logging.INFO, f"Received ACK, setting got ACK, MSG:{msg}")
                    with self.sem:
                        self._got_ack = True
                elif msg.msg_type == MSG_RCK:
                    logging.log(logging.INFO, f"Received RCK, setting got REC ACK, MSG:{msg}")
                    with self.sem:
                        if self._sending_recovery:
                            self._got_rec_ack = True
                elif msg.msg_type == MSG_TOK:
                    logging.log(logging.INFO, f"Received TOK, sending ACK, MSG:{msg}")
                    with self.sem:
                        if msg.turn == self._turn:
                            self._has_token = True
                            self._got_ack = True

                    res = Message(self.rank, msg.src, MSG_ACK, "OK", msg.turn)
                    self.send(msg.src, res)
                elif msg.msg_type == MSG_REC:
                    logging.log(logging.INFO, f"Received REC, sending RCK, MSG:{msg}")
                    res = Message(self.rank, msg.src, MSG_RCK, "RECOK", msg.turn)
                    self.send(msg.src, res)
                    # If token was for us and for current turn then create token
                    if msg.dest == self.rank:
                        if msg.turn == self._turn:
                            self._has_token = True
                        else:
                            pass
                    else: # If token was not for us then pass it through
                        if self._has_token:
                            pass
                        sending_recovery = False
                        with self.sem:
                            sending_recovery = self._sending_recovery
                        if not sending_recovery: # If we are not passing token already
                            with self.sem:
                                self._sending_recovery = True
                            send_left = False

                            if msg.src > self.rank:
                                if msg.src == self.node_count - 1 and self.rank == 0:
                                    send_left = False
                                else:
                                    send_left = True
                            else:
                                if msg.src == 0 and self.rank == self.node_count - 1:
                                    send_left = True
                                else:
                                    send_left = False
                            
                            pass_recovery_thread = threading.Thread(target = self.pass_recovery_token, args=[msg.dest, msg.turn, send_left])
                            pass_recovery_thread.start()
                else:
                    logging.log(logging.INFO, f"Received unknown message_type, MSG:{msg}")
        receiver_thread = threading.Thread(target = __receiver)
        receiver_thread.start()

    def enter_section(self):
        logging.log(logging.INFO, f"Waiting for critical section...")
        has_token = False
        with self.sem:
            has_token = self._has_token
        while not has_token:
            sleep(1)
            with self.sem:
                has_token = self._has_token
        logging.log(logging.INFO, f"Entering critical section")

    def leave_section(self):
        self.pass_token()
        logging.log(logging.INFO, f"Leaving critical section")

    def run_pass_token(self):
        pass_token_thread = threading.Thread(target = self.pass_token)
        pass_token_thread.start()

    def pass_token(self):
        has_token = False
        with self.sem:
            has_token = self._has_token
        if has_token:
            with self.sem:
                self._has_token = False
            turn = self._turn
            if self.rank == self.node_count - 1:
                turn = ((self._turn + 1) % 2)

            msg = Message(self.rank, (self.rank + 1) % self.node_count, MSG_TOK, "TOKEN", turn)
            receiver_no = (self.rank + 1) % self.node_count
            self.send(receiver_no, msg)
            sleep(2)

            got_ack = False
            with self.sem:
                got_ack = self._got_ack
            if not got_ack:
                pass_recovery_thread = threading.Thread(target = self.pass_recovery_token, args=[receiver_no, turn, True])
                pass_recovery_thread.start()
            else:
                with self.sem:
                    self._got_ack = None

            self._turn = ((self._turn + 1) % 2)
        else:
            logging.log(logging.INFO, f"Doesn't have the token! (so he can't pass it)")

    def pass_recovery_token(self, msg_dest, msg_turn, send_left=True):
        got_rec_ack = False
        with self.sem:
            got_rec_ack = self._got_rec_ack
        while not got_rec_ack:
            self._sending_recovery = True
            receiver_no = -1
            if send_left:
                receiver_no = (self.node_count - 1) if (self.rank == 0) else (self.rank - 1)
            else:
                receiver_no = (self.rank + 1) % self.node_count

            msg = Message(self.rank, msg_dest, MSG_REC, "RECOVERY", msg_turn)
            self.send(receiver_no, msg)
            logging.log(logging.INFO, f"Sending RECOVERY to {receiver_no}, MSG:{msg}")
            send_left = not send_left
            sleep(2)
            with self.sem:
                got_rec_ack = self._got_rec_ack
        with self.sem:
            self._sending_recovery = False
            self._got_rec_ack = None

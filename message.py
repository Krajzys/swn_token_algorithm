MSG_UND = 0 # Undefined
MSG_ACK = 1 # Acknowledge
MSG_TOK = 2 # Ordinary token
MSG_REC = 3 # Recovery token
MSG_RCK = 4 # Recovery ack

class Message:
    def __init__(self):
        self.src = 0
        self.dest = 0
        self.data = ""
        self.msg_type = 0
        self.turn = 0

    def __init__(self, src, dest, msg_type, data, turn):
        self.src = src
        self.dest = dest
        self.msg_type = msg_type
        self.data = data
        self.turn = turn

    def __repr__(self):
        return f"Message{{src={self.src},dest={self.dest},msg_type={self.msg_type},data={self.data},turn={self.turn}}}"

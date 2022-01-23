# SWN Token Algorithm

A simple token ring mutual exclusion algorithm.

## Explanation

This algorithm works in the following way:

1. Node with the token can enter critical section.
1. Then it passes the token to the right (MSG_TOK message).
1. Receiver replies with an MSG_ACK message.
1.  If the sender doesn't receive a reply he will send a MSG_REC recovery token in the other way (so initially to the left).
1. If the sender doesn't receive a MSG_RCK message until timeout it send the message in the other direction.
1. Node receiving a MSG_REC token checks if the token is intended for them:
    - YES: it creates a token and gains Critical section access.
    - NO: it passes the token along in the direction it was heading and waits for REC_ACK message.

## Usage and arguments

```
usage: main.py [-h] [-l LOG] [--no-acks] [-s SUCCESS_RATE]

options:
  -h, --help            show this help message and exit
  -l LOG, --log LOG     Specifies file to which logs should be saved
  --no-acks             Specifies that no acks should be accepted
  -s SUCCESS_RATE, --success-rate SUCCESS_RATE
                        Specifies the chance that the message will be sent. 0.9 is 90% etc.
```

This program should be run with mpiexec, so for example:

`mpiexec -n 4 python main.py -l info.log --no-acks`
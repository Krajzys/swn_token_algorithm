# SWN Token Algorithm

A simple token ring mutual exclusion algorithm.

## Usage and arguments

```
usage: main.py [-h] [-l LOG] [--no-acks] [-s SUCCESS_RATE]

options:
  -h, --help            show this help message and exit
  -l LOG, --log LOG     Specifies file to which logs should be saved
  --no-acks             Specifies that no acks should be accepted
  -s SUCCESS_RATE, --success-rate SUCCESS_RATE
                        Specifies the chance that the message won't be sent
```

This program should be run with mpiexec, so for example:

`mpiexec -n 4 python main.py -l info.log --no-acks`
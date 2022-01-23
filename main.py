from mpi4py import MPI
import node as nd
import time
import random
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--log', type=str, help="Specifies file to which logs should be saved", required=False)
    parser.add_argument('--no-acks', action="store_true", help="Specifies that no acks should be accepted", required=False)
    parser.add_argument('-s', '--success-rate', type=float, help="Specifies the chance that the message won't be sent", required=False)

    args = parser.parse_args()

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    count = comm.Get_size()

    log_file_name = ""
    success_rate = 1
    no_acks = False
    if args.log:
        log_file_name = args.log
    if args.success_rate:
        success_rate = args.success_rate
    if args.no_acks:
        no_acks = True

    node = nd.Node(rank, comm, count, log_file=log_file_name, success_rate = success_rate, no_acks=no_acks)
    if node.rank == 0:
        node._has_token = True

    while True:
        if random.random() > 0.3:
            print(f"{rank} wants to enter section", flush=True)
            node.enter_section()
            print(f"{rank} is inside the critical section", flush=True)
            time.sleep(5)
            node.leave_section()
            print(f"{rank} leaves critical section", flush=True)
            time.sleep(2)
        else:
            node.run_pass_token()
            print(f"{rank} sleeps for 10s", flush=True)
            time.sleep(10)

if __name__ == '__main__':
    main()
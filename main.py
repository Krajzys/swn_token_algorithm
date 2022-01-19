from mpi4py import MPI
import node as nd
import time

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
count = comm.Get_size()

if rank == 0:
    node = nd.Node(rank, comm, count)
elif rank == 1:
    node = nd.Node(rank, comm, count, deny_from=[0])
else:
    node = nd.Node(rank, comm, count)

if node.rank == 0:
    node._has_token = True

node.enter_section()
time.sleep(5)
node.leave_section()

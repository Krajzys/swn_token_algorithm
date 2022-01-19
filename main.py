from mpi4py import MPI
import message as msg
import node as nd

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
count = comm.Get_size()

print(count)
exit(2)

if rank == 0:
    node = nd.Node(rank, comm, count)
else:
    node = nd.Node(rank, comm, count, 0.9)

if node.rank == 0:
    message = msg.Message(node.rank, 1, msg.MSG_UND, "Token magic", 0)
    node.sure_send(1, message)

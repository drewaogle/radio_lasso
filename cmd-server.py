import zmq
import ipc_pb2
import time
import threading

act= ipc_pb2.IPC.Action
def message( action, string=None, blob=None ):
    out = ipc_pb2.IPC()
    out.action = int(action)
    if string is not None:
        out.str_data = string
    if blob is not None:
        out.blob_data = blob
    return out.SerializeToString()

def rmessage( blob ):
    out = ipc_pb2.IPC()
    out.ParseFromString(blob)
    return out

def get_or_die( s,  action ):
    msg = s.recv()
    ipcm = rmessage(msg)
    if ipcm.action != action:
        raise Exception("Bad State")

def cmd_server( port ):
    print(f"Starting command server on {port}")
    ctx = zmq.Context()
    socket = ctx.socket(zmq.REQ)
    #socket = ctx.socket(zmq.REP)
    #socket.bind(f"tcp://127.0.0.1:{port}")
    socket.bind(f"tcp://localhost:{port}")

    print("Waiting for client")
    socket.send(message(act.STARTED))
    print("Sent hi")
    get_or_die(socket,act.STARTED)


    def do_log( string ):
        print(string)


    i = 10

    do_log("Starting Audio Command Server")

    working = True
    while working:
        i = i - 1
        if i > 0:
            socket.send(message(act.PING))
            get_or_die(socket,act.PONG)
            time.sleep(1)
        else:
            socket.send(message(act.STOP))
            working = False
    print("Done")
    socket.close()

cmd_server( 5788 )

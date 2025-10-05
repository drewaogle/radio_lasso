import zmq
import ipc_pb2

act= ipc_pb2.IPC.Action

print("Starting Audio Device")

def message( action, string=None, blob=None ):
    out = ipc_pb2.IPC()
    out.action = action
    if string is not None:
        out.str_data = string
    if blob is not None:
        out.blob_data = blob
    return out.SerializeToString()

def rmessage( blob ):
    out = ipc_pb2.IPC()
    out.ParseFromString(blob)
    return out

if __name__ == "__main__":
    ctx = zmq.Context()
    socket = ctx.socket(zmq.REP)
    socket.connect("tcp://localhost:5788")

    msg = socket.recv()
    ipcm = rmessage(msg)
    if ipcm.action == act.STARTED: 
        print("Ok, connected")
        socket.send(message(act.STARTED))
    else:
        raise Exception("main:IPC Init Fail")
    
    working = True
    while working:
        msg = socket.recv()
        ipcm = rmessage(msg)
        if ipcm.action == act.PING: 
            print("main: server is alive") 
            socket.send(message(act.PONG))
        if ipcm.action == act.AUDIO_CMD: 
            print(f"main: command requested for audio device {ipcm.string}")
            socket.send(message(act.PONG))
        elif ipcm.action == act.STOP: 
            print("main: server is done")
            working = False
        else:
            raise Exception("main: IPC Init PING Fail")
    print("exiting")

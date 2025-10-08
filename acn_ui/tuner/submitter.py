import zmq
import tuner.ipc_pb2
import time
import json

import sys

act= tuner.ipc_pb2.IPC.Action



def message( action, string=None, blob=None ):
    out = tuner.ipc_pb2.IPC()
    out.action = action
    if string is not None:
        out.str_data = string
    if blob is not None:
        out.blob_data = blob
    return out.SerializeToString()

def rmessage( blob ):
    out = tuner.ipc_pb2.IPC()
    out.ParseFromString(blob)
    return out

def submit_audio_cmd( cmdtype, cmdarg):

    print("AUDIO CMD")
    ctx = None
    ok = False
    try:
        ctx = zmq.Context()
        socket = ctx.socket(zmq.REQ)
        socket.connect("tcp://localhost:5760")

        poller = zmq.Poller()
        #poller.register(socket, zmq.POLLOUT)
        poller.register(socket, zmq.POLLIN)

        #socks = dict(poller.poll(1000))

        info = {
                "cmd": f"{cmdtype} {cmdarg}"
                }

        try:
            socket.send(message(act.AUDIO_CMD, string=json.dumps(info)), flags = zmq.NOBLOCK)
            socks = dict(poller.poll(1000))
            print(f"Results = {socks}")
            if socket in socks and socks[socket] == zmq.POLLIN:
                print("Ok to receive Audio Result")
                state = act.STARTED
                msg = socket.recv()
                ipcm = rmessage(msg)
                print("Done")
                ok = True
            else:
                print("Unable to get result from Command!!")
        except Exception as e:
            print("Unable to send Command!!")
    finally:
        print("submit_audio_cmd: cleanup")
        if ctx is not None:
            ctx.destroy()
            #ctx.term() if ok else ctx.destroy()
    return ok
    

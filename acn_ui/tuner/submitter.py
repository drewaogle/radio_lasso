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
    ctx = zmq.Context()
    socket = ctx.socket(zmq.REQ)
    socket.connect("tcp://localhost:5760")

    info = {
            "cmd": f" {cmdtype} {cmdarg}"
            }
    socket.send(message(act.AUDIO_CMD, string=json.dumps(info)))
    state = act.STARTED
    msg = socket.recv()
    ipcm = rmessage(msg)
    

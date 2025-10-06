# requestor.py - send requests to server to send to one or more clients.
import zmq
import ipc_pb2
import time
import json

import sys

act= ipc_pb2.IPC.Action

from argparse import ArgumentParser

def get_args():
    p = ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("-s","--stop",default=False)
    g.add_argument("-c","--command",nargs=1,default=True)

    args = p.parse_args()
    return args


print("Starting Requester")

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

    args = get_args()
    print(args)
    ctx = zmq.Context()
    socket = ctx.socket(zmq.REQ)
    socket.connect("tcp://localhost:5760")

    info = {
            "cmd": args.command[0]
            }
    socket.send(message(act.AUDIO_CMD, string=json.dumps(info)))
    state = act.STARTED
    msg = socket.recv()
    ipcm = rmessage(msg)
    
    print("exiting")

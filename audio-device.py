import zmq
import ipc_pb2
import time
import json

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
    socket = ctx.socket(zmq.REQ)
    socket.connect("tcp://localhost:5788")

    state = act.STARTED

    running = True
    audio_id = None

    while running:
        time.sleep(.5)
        if state == act.STARTED:
            socket.send(message(act.STARTED))
            msg = socket.recv()
            ipcm = rmessage(msg)
            if ipcm.action == act.STARTED: 
                info = json.loads(ipcm.str_data)
                print(f"Ok, connected id == {info['id']} ")
                audio_id = info["id"]
            else:
                raise Exception("main:IPC Init Fail")
            state = act.PING
        else:
            print("Sending ping...")
            info = { "id": audio_id }
            socket.send(message(act.PING, string=json.dumps(info) ))
            msg = socket.recv()
            ipcm = rmessage(msg)
            if ipcm.action == act.PONG: 
                print("main: server is alive") 
                try:
                    data = json.loads(ipcm.str_data)
                    print(f"Status is {data['status']}")
                except:
                    print(f"woops, bad status: {ipcm.str_data}")
            elif ipcm.action == act.AUDIO_CMD: 
                print(f"main: command requested for audio device {ipcm.string}")
                socket.send(message(act.PONG))
            elif ipcm.action == act.STOP: 
                print("main: server has requested stop")
                running = False
            else:
                print(f"audio: uhh .. unknown command? {ipcm.action}")

    
    print("exiting")

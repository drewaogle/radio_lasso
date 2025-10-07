import zmq
import ipc_pb2
import time
import json
import subprocess
from pathlib import Path
from pydantic import BaseModel,Field,model_validator
from typing import Annotated,Optional
from typing_extensions import TypedDict
from argparse import ArgumentParser

act= ipc_pb2.IPC.Action

class PlaylistItem(TypedDict):
    name:str
    url:str

class ActionItem(BaseModel):
    name:str
    script:Optional[str] = None
    python:Optional[str] = None
    @model_validator(mode="after") 
    def only_one_sink(self): 
        if (self.script and self.python) or (not self.script and not self.python) :
                raise ValueError("Requires either 'python' or 'script'")
        return self

class Config(BaseModel):
    host:str
    port:Annotated[int,Field(gt=0,lt=65536)]
    poll_sec:float
    playlists:list[PlaylistItem] = None
    actions:list[ActionItem] =None



default_cfg = {
        "host":"localhost",
        "port":5788,
        "poll_sec":0.5
        }

def get_args():
    p = ArgumentParser()
    p.add_argument("-C","--config",default="/etc/acn/device.conf.json")

    args = p.parse_args()
    return args

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

def do_command( command, playlists, actions ):

    def _run( ccfg, parts ):
        if ccfg["cfg"].python:
            ccfg["func"]( *parts )
        else:
            #subprocess.run( [ ccfg["cfg"].script ] + parts, capture_output=True )
            proc = subprocess.Popen( [ ccfg["cfg"].script ] + parts, shell=False) 
            proc.communicate() 


    cparts = command.split()
    if cparts[0] == "playlist":
        if len(cparts) != 2:
            print("Playlist command takes 2 args.")
            return
        if not "playlist" in actions:
            print("No action for playlist") 
            return
        if not cparts[1] in playlists:
            print(f"No playlist for {cparts[1]}")
            return
        _run(actions["playlist"], [ playlists[cparts[1]]["url"]])
        pass
    elif cparts[0] == "player":
        if len(cparts) != 2:
            print("Player command takes 2 args.")
            return
        if not "player" in actions:
            print("No action for player") 
            return
        _run(actions["player"], [ cparts[1]])
        pass
    else:
        print(f"Bad Command {cparts[0]}")

if __name__ == "__main__":
    args= get_args()
    cfg = Path(args.config)
    if cfg.exists():
        with open(cfg) as fp:
            opts = Config.model_validate_json(fp.read())
    else:
        opts = Config.model_validate_json(json.dumps(default_cfg))

    playlist_by_name = {}
    if opts.playlists:
        playlist_by_name = { itm["name"]: itm  for itm in opts.playlists }
    cmd_by_name = {} 
    if opts.actions:
        cmd_by_name = { itm.name: {"cfg": itm } for itm in opts.actions }
        import importlib
        import re
        for k in cmd_by_name.keys():
            # verify all python loads
            try:
                if cmd_by_name[k]["cfg"].python:
                    cs = re.match("^(.*)\.(.*)",cmd_by_name[k]["cfg"].python)
                    #print( f"cs = {cs} {cs.group(1)}, {cs.group(2)}")
                    act_mod = cs.group(1)
                    act_func = cs.group(2)
                    mod = importlib.import_module( act_mod )
                    act_runner = getattr(mod,act_func)
                    cmd_by_name[k]["func"] = act_runner
                # verify shell script exists.
                else:
                    script = cmd_by_name[k]["cfg"].script 
                    if not Path( script ).exists(): 
                        raise Exception(f"Configured script for {k} is {script}, but doesn't exist.")
            except Exception as e:
                print("Failed to verify actions work")
                sys.exit(1)



    print(f"Starting Audio Device; Server is {opts.host}:{opts.port}")
    print(f"Registered Actions for: " + " ".join( cmd_by_name.keys()))
    print(f"Playlists for: " + " ".join( playlist_by_name.keys()))
    ctx = zmq.Context()
    socket = ctx.socket(zmq.REQ)
    socket.connect(f"tcp://{opts.host}:{opts.port}")

    state = act.STARTED

    running = True
    audio_id = None

    while running:
        time.sleep(opts.poll_sec)
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
            #print("Sending ping...")
            info = { "id": audio_id }
            socket.send(message(act.PING, string=json.dumps(info) ))
            msg = socket.recv()
            ipcm = rmessage(msg)
            if ipcm.action == act.PONG: 
                #print("main: server is alive") 
                try:
                    data = json.loads(ipcm.str_data)
                    #print(f"Status is {data['status']}")
                except:
                    print(f"woops, bad status: {ipcm.str_data}")
            elif ipcm.action == act.AUDIO_CMD: 
                data = json.loads(ipcm.str_data)
                if "commands" in data:
                    for c in data["commands"]:
                        do_command(c, playlist_by_name, cmd_by_name )
                else:
                    print(f"main: command requested for audio device, but unknown: {ipcm.str_data}")
            elif ipcm.action == act.STOP: 
                print("main: server has requested stop")
                running = False
            else:
                print(f"audio: uhh .. unknown command? {ipcm.action}")

    
    print("exiting")

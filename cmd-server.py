import zmq
import ipc_pb2
import time
import threading
import json

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


proxy_running = False
audio_running = False

lock = threading.Lock()
proxied_list = []

def cmd_proxy_thread( port ):
    print(f"Starting Proxy thread on {port}")
    proxy_running = True
    ctx = zmq.Context()
    socket = ctx.socket(zmq.REP)
    socket.bind(f"tcp://localhost:{port}")

    while proxy_running:

        msg = s.recv()
        ipcm = rmessage(msg)
        if ipcm.action == act.STARTED:
            socket.send(message(act.STARTED))
        elif ipcm.action == act.AUDIO_CMD:
            lock.acquire()
            try:
                proxied_list.append( ipcm.str_data )
                pass
            finally:
                lock.release()




# req socker must receive first
# rep socket must send first.

# easiest thing here is have clients
# send req to server on timers

def do_log( string ):
    print(string)

def cmd_server( port ):
    print(f"Starting command server on {port}")
    audio_running = True
    ctx = zmq.Context()
    socket = ctx.socket(zmq.REP)
    # older version can't take localhost, must have 127.0.0.1
    # 25.1.1 vs 27.1.0?
    #socket.bind(f"tcp://127.0.0.1:{port}")
    socket.bind(f"tcp://localhost:{port}")

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLOUT)
    poller.register(socket, zmq.POLLIN)

    client_state = {}

    client_stamp = 0

    ## TODO Catch SIGTERM

    loops = 0

    do_log("Starting Audio Command Server")
    while audio_running:
        socks = dict(poller.poll(100))
        # have a client ready to send a message to
        if socket in socks and socks[socket] == zmq.POLLIN:
            msg = socket.recv()
            ipcm = rmessage(msg)
            if ipcm.action == act.STARTED:
                do_log("New client, sending id.") 
                client_stamp = client_stamp + 1
                info = { "id": client_stamp }
                socket.send(message(act.STARTED,string=json.dumps(info)))
                client_state[client_stamp]=act.STARTED
            elif ipcm.action == act.PING:
                if ipcm.str_data is None or ipcm.str_data == "":
                    do_log("client pin - bad!")
                    do_log("No Data in ping - malformed.")
                    info = {"error":"malformed ping, no id. DISCONNECT"}
                    socket.send(message(act.STOP,string=json.dumps(info))) 
                else:
                    try:
                        client_info = json.loads(ipcm.str_data)
                        clid = client_info["id"]
                        do_log(f"client ping from {clid}")
                        info={"status": "no update" }
                        socket.send(message(act.PONG,string=json.dumps(info))) 
                    except:
                        do_log(f"client ping bad data = {ipcm.str_data}")
                        info = {"error":"malformed ping, no id. DISCONNECT"}
                        socket.send(message(act.STOP,string=json.dumps(info))) 

            else:
                do_log("Bad action - malformed.")
                info = {"error":"malformed action - not supported. DISCONNECT"}
                socket.send(message(act.STOP,string=json.dumps(info)))


        loops = loops + 1 
        if loops % 20 == 0: 
            loops = 0 
            do_log("Check for local data now")




    i = 10


    do_log("Done Server")
    socket.close()

#proxy_thread = threading.Thread( target=cmd_proxy_thread, args=(5760,))
cmd_server( 5788 )

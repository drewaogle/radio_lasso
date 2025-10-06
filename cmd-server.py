import zmq
import ipc_pb2
import time
import threading
import json
import sys
import signal




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
die_fast = False
really_die = False

lock = threading.Lock()
proxied_list = []

def sigint_handler(sig, frame):
    global really_die,die_fast,proxy_running,audio_running
    if really_die:
        print("Ok, gotcha lady, shutting down now")
        sys.exit(0)
    # if they press it twice, just do it.
    really_die = True
    die_fast = True
    print("Caught SIGNINT, shutting down..")
    proxy_running = False
    audio_running = False


signal.signal(signal.SIGINT, sigint_handler)

def cmd_proxy_thread( port ):
    global proxy_running
    print(f"Starting Proxy thread on {port}")
    proxy_running = True
    ctx = zmq.Context()
    socket = ctx.socket(zmq.REP)
    socket.bind(f"tcp://localhost:{port}")

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    loops = 0 
    while proxy_running:
        socks = dict(poller.poll(1000))
        if socket in socks and socks[socket] == zmq.POLLIN:
            msg = socket.recv()
            ipcm = rmessage(msg)
            if ipcm.action == act.AUDIO_CMD:
                print("Got Audio Command")
                lock.acquire()
                try:
                    proxied_list.append( ipcm.str_data )
                finally:
                    lock.release()
                info={"status": "sent" } 
                socket.send(message(act.AUDIO_CMD,string=json.dumps(info))) 
            elif ipcm.action == act.STOP:
                audio_running = False
                info={"status": "sent" } 
                socket.send(message(act.AUDIO_CMD,string=json.dumps(info))) 
                # allows server time to notify clients.

        loops = loops + 1 
        if loops % 10 == 0: 
            loops = 0 
            #print("Checking proxy Cont")





# req socker must receive first
# rep socket must send first.

# easiest thing here is have clients
# send req to server on timers

def do_log( string ):
    print(string)

def cmd_server( port ):
    global audio_running,proxied_list
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
    local_list = []

    responsive_clients = {}

    cmd_for_client = {}

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
                responsive_clients[client_stamp]=int(time.monotonic())
                info = { "id": client_stamp }
                cmd_for_client[client_stamp]=[]
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
                        clid = int(client_info["id"])
                        responsive_clients[clid]=int(time.monotonic())
                        #do_log(f"client ping from {clid}")
                        if len(cmd_for_client[clid]) == 0:
                            info={"status": "no update" }
                            socket.send(message(act.PONG,string=json.dumps(info))) 
                        else:
                            print("sending cmd")
                            info = {"commands":cmd_for_client[clid]}
                            socket.send(message(act.AUDIO_CMD,string=json.dumps(info))) 
                            cmd_for_client[clid] = []

                    except Exception as e:
                        do_log(e)
                        do_log(f"client ping bad data = {ipcm.str_data}")
                        info = {"error":"malformed ping, no id. DISCONNECT"}
                        socket.send(message(act.STOP,string=json.dumps(info))) 

            else:
                do_log("Bad action - malformed.")
                info = {"error":"malformed action - not supported. DISCONNECT"}
                socket.send(message(act.STOP,string=json.dumps(info)))




        loops = loops + 1 
        if loops % 10 == 0:
            ejected = []
            for c,t in responsive_clients.items():
                time_window = t + 10
                cur_time = int(time.monotonic())
                if time_window < cur_time: 
                    print(f"Client {c} is no longer responsive  {time_window} < {cur_time}")
                    ejected.append(c)
            for e in ejected:
                print(f"Dropped {e}")
                del responsive_clients[e]
                del cmd_for_client[e]

        lock.acquire()
        try:
            if len(proxied_list) != 0:
                print("Copying commands")
                local_list.extend(proxied_list)

                if len(responsive_clients) == 0:
                    print("No clients to send commands to. Dumping")
                    local_list = []
                else:
                    print(f"Adding {local_list}")
                    for k in cmd_for_client.keys():
                        cmd_for_client[k] = cmd_for_client[k] + [json.loads(i)["cmd"] for i in local_list]
                        print(f"Ready to send commands:  {cmd_for_client[k]} to {k}") 
                proxied_list = []
                local_list = []
        finally:
            lock.release()




    i = 10


    do_log("Done Server")
    socket.close()
    proxy_running = False

proxy_thread = threading.Thread( target=cmd_proxy_thread, args=(5760,))
proxy_thread.start()
cmd_server( 5788 )

proxy_thread.join()

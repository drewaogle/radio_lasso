import zmq
import ipc_pb2
import time
import threading
import json
import sys
import signal
import logging
import daemon

DEFAULT_FORMAT= "%(asctime)s %(levelname)s - %(funcName)s :: %(message)s"
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, format=DEFAULT_FORMAT)


daemon_fhs=[]

from argparse import ArgumentParser

def set_loggers(args):
        for h in logger.handlers[:]:
            logger.removeHandler(h)
        fmt = logging.Formatter( DEFAULT_FORMAT )
        logfile =  args.logfile if args.logfile is not None else "/tmp/acn-server.log"
        fh = logging.FileHandler( logfile )
        daemon_fhs.append(fh.stream.fileno())
        fh.setFormatter(fmt)
        fh.setLevel(logging.INFO)
        logger.addHandler(fh)

def get_args():
    p = ArgumentParser()
    #g = p.add_mutually_exclusive_group(required=True)
    p.add_argument("-D","--no-daemonize",action="store_true",default=False)
    p.add_argument("--logfile",default=None)

    args = p.parse_args()
    # log to file if daemonizing.
    if not args.no_daemonize or args.logfile:
        set_loggers(args)
    return args


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
        logger.warning("Ok, gotcha lady, shutting down now")
        sys.exit(0)
    # if they press it twice, just do it.
    really_die = True
    die_fast = True
    logger.warning("Caught SIGNINT, shutting down..")
    proxy_running = False
    audio_running = False


signal.signal(signal.SIGINT, sigint_handler)

def cmd_proxy_thread( port ):
    global proxy_running
    logger.info(f"Starting Proxy thread on {port}")
    proxy_running = True
    ctx = zmq.Context()
    socket = ctx.socket(zmq.REP)
    socket.bind(f"tcp://localhost:{port}")

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    loops = 0 
    while proxy_running:
        socks = dict(poller.poll(500))
        if socket in socks and socks[socket] == zmq.POLLIN:
            msg = socket.recv()
            ipcm = rmessage(msg)
            to_send = None
            if ipcm.action == act.AUDIO_CMD:
                logger.info("Got Audio Command")
                lock.acquire()
                try:
                    proxied_list.append( ipcm.str_data )
                finally:
                    lock.release()
                info={"status": "sent" } 
                to_send= json.dumps(info)
            elif ipcm.action == act.STOP:
                audio_running = False
                info={"status": "sent" } 
                to_send= json.dumps(info)
                # allows server time to notify clients.

            if to_send is not None:
                try:
                    socket.send(message(act.AUDIO_CMD,string=to_send), flags=zmq.NOBLOCK)
                except Exception as e:
                    logger.warning("Unable to send result to proxy client")
        else:
            pass
            #logger.info(f"Nothing in {socks}")

        loops = loops + 1 
        if loops % 500 == 0: 
            loops = 0 
            logger.info("proxy active")
            #print("Checking proxy Cont")





# req socker must receive first
# rep socket must send first.

# easiest thing here is have clients
# send req to server on timers


def cmd_server( port ):
    global audio_running,proxied_list
    logger.info(f"Starting command server on {port}")
    audio_running = True
    ctx = zmq.Context()
    socket = ctx.socket(zmq.REP)
    # older version can't take localhost, must have 127.0.0.1
    # 25.1.1 vs 27.1.0?
    #socket.bind(f"tcp://127.0.0.1:{port}")
    socket.bind(f"tcp://*:{port}")

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

    logger.info("Starting Audio Command Server")
    while audio_running:
        socks = dict(poller.poll(100))
        # have a client ready to send a message to
        if socket in socks and socks[socket] == zmq.POLLIN:
            msg = socket.recv()
            ipcm = rmessage(msg)
            if ipcm.action == act.STARTED:
                logger.info("New client, sending id.") 
                client_stamp = client_stamp + 1
                responsive_clients[client_stamp]=int(time.monotonic())
                info = { "id": client_stamp }
                cmd_for_client[client_stamp]=[]
                socket.send(message(act.STARTED,string=json.dumps(info)))
                client_state[client_stamp]=act.STARTED
            elif ipcm.action == act.PING:
                if ipcm.str_data is None or ipcm.str_data == "":
                    logger.info("client pin - bad!")
                    logger.info("No Data in ping - malformed.")
                    info = {"error":"malformed ping, no id. DISCONNECT"}
                    socket.send(message(act.STOP,string=json.dumps(info))) 
                else:
                    try:
                        client_info = json.loads(ipcm.str_data)
                        clid = int(client_info["id"])
                        responsive_clients[clid]=int(time.monotonic())
                        to_send = None
                        if len(cmd_for_client[clid]) == 0:
                            info={"status": "no update" }
                            cmd = act.PONG
                            to_send= json.dumps(info)
                        else:
                            logger.info("sending cmd")
                            info = {"commands":cmd_for_client[clid]}
                            cmd = act.AUDIO_CMD
                            to_send= json.dumps(info)
                            cmd_for_client[clid] = []

                        if to_send is not None:
                            # shouldn't need to worry about blocking here
                            socket.send(message(cmd,string=to_send))


                    except Exception as e:
                        logger.error(e)
                        logger.error(f"client ping bad data = {ipcm.str_data}")
                        info = {"error":"malformed ping, no id. DISCONNECT"}
                        socket.send(message(act.STOP,string=json.dumps(info))) 

            else:
                logger.warning("Bad action - malformed.")
                info = {"error":"malformed action - not supported. DISCONNECT"}
                socket.send(message(act.STOP,string=json.dumps(info)))




        loops = loops + 1 
        if loops % 10 == 0:
            ejected = []
            for c,t in responsive_clients.items():
                time_window = t + 10
                cur_time = int(time.monotonic())
                if time_window < cur_time: 
                    logger.warning(f"Client {c} is no longer responsive  {time_window} < {cur_time}")
                    ejected.append(c)
            for e in ejected:
                logger.warning(f"Dropped data for client {e}")
                del responsive_clients[e]
                if e in cmd_for_client:
                    del cmd_for_client[e]

        if loops % 500 == 0:
            logger.info("command active")
            loops = 0

        lock.acquire()
        try:
            if len(proxied_list) != 0:
                logger.debug("Copying commands")
                local_list.extend(proxied_list)

                if len(responsive_clients) == 0:
                    logger.info("No clients to send commands to. Dumping")
                    local_list = []
                else:
                    logger.info(f"Adding {local_list}")
                    for k in cmd_for_client.keys():
                        cmd_for_client[k] = cmd_for_client[k] + [json.loads(i)["cmd"] for i in local_list]
                        logger.info(f"Ready to send commands:  {cmd_for_client[k]} to {k}") 
                proxied_list = []
                local_list = []
        finally:
            lock.release()




    i = 10


    logger.info("Done Server")
    socket.close()
    proxy_running = False

args = get_args()

def main():
    proxy_thread = threading.Thread( target=cmd_proxy_thread, args=(5760,))
    proxy_thread.start()
    cmd_server( 5788 )

    proxy_thread.join()

if args.no_daemonize:
    main()
else:
    ctx = daemon.DaemonContext()
    ctx.files_preserve = daemon_fhs
    with ctx:
        main()

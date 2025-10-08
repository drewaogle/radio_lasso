# RadioLasso
Keep your remote radio devices managed.

# What is it
RL is a set of 3 items, which allow you to control remote radio devices.
- Web app
- Command server
- Audio device poller

The main loop is the command server; it sits on the same system (ish?) as the
web app, and collects request for radio devices.

The radio devices connect to the command server, and receive instructions.


## Instructions
First, it gets set up, then you use the webapp to control your radio!
### Webapp
acn_ui gets set up on a server, `uwsgi --ini <the_ini>` is an easy way.
then you add passing the context from your webserver ( such as nginx/apache )

### Control Master
This should also run on the same server, or at least network as the webapp.
The key item this needs is the ability for the audio device to connect.
just run it with `python cmd-server.py` and it will run in the background.

### Audio Device
This runs on your audio device/radio. It should usually be configured with the
json config file.

host and port for the controller are required.
Other than that, just define playlist actions which just allow you to keep the 
"how do I convert 'morning' to my playlist" - so that if you switch it, you only
have to do it right at the device.

The last critical thing is making the actions for your device; it can be python
code, or a shell script. The action section has what to expect.

# Actions
Right now the instructions are
- playlist <name>
- player <play|pause|next|previous>

But .. you could add anything you want.

Audio device allows you to map the names into urls or whatever you want on a
specific host.

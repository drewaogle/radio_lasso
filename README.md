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
Right now the instructions are
- playlist <name>
- player <play|pause|next|previous>

But .. you could add anything you want.

Audio device allows you to map the names into urls or whatever you want on a
specific host.

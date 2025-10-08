tar: acn.tar.gz
client: acn-client.tar.gz

acn.tar.gz:
	tar -zcvf acn.tar.gz *.py *.txt acn_ui
acn-client.tar.gz:
	tar -zcvf acn-client.tar.gz audio-device.py ipc_pb2.py local_audio_commands

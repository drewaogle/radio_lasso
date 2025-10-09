server: acn.tar.gz
client: acn-client.tar.gz
test:
	find . -path "./*.py" -o -path "./acn_ui/*" -a -not -path "*__pycache__*" -a -not -name db.sqlite3
acn.tar.gz:
	mkdir -p tmp/server/
	find . \( -path "./*.py" -o -path "./acn_ui/*" -a -not -path "*__pycache__*" -a -not -name db.sqlite3 \) -a  -exec ./mkdir_and_cp.sh {} tmp/server/ \;
	tar -C tmp -zcvf acn.tar.gz server
	rm -rf tmp
acn-client.tar.gz:
	tar -zcvf acn-client.tar.gz audio-device.py ipc_pb2.py local_audio_commands

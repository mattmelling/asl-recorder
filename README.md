Records a USRP stream to OGG files.

## Installation
```
git clone https://github.com/mattmelling/asl-recorder/ /opt/asl-recorder
cd /opt/asl-recorder
```
### Prerequisites
```
apt-get install python3-venv python3-pip libogg-dev libopusenc-dev libflac-dev libopusfile-dev libopus-dev libvorbis-dev libopus0
```
### Virtual Environment
```
cd /opt/asl-recorder
python -m venv venv
```
### Install `pyogg`
Current version of pyogg available through pip is not up to date, so install from git.
```
cd /opt
git clone https://github.com/TeamPyOgg/PyOgg.git
cd PyOgg
/opt/asl-zello-bridge/venv/bin/python setup.py install
```
### Install recorder
```
cd /opt/asl-recorder
venv/bin/pip install .
cp asl-recorder.service /etc/systemd/system/
systemctl edit asl-recorder.service # (see Environment Variables)
systemctl enable asl-recorder.service
```

## Environment variables
If using the included service definition, use `systemctl edit` to set these.

E.g.

```
[Service]
Environment=USRP_BIND=127.0.0.1
```

- `USRP_BIND`: IP address to bind to for USRP stream
- `USRP_RXPORT`: Port to listen on for USRP stream
- `RECORDING_PATH`: Where to save files
- `RECORDING_TTL`: How long to keep files

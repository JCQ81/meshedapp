# MeshedApp

A simple web interface for your Meshtastic chat centrally hosted on your home server. 

![](./img/example1.png)

## Setup

Example setup for RHEL9 based systems (AlmaLinux 9 / Rocky Linux 9)

```
dnf -y install git python3 python3-flask python3-pip python3-waitress
pip install meshtastic
git clone https://github.com/JCQ81/meshedapp.git
cd meshedapp
./meshedapp.py [meshtastic-device-ip]
```

Now browse to [http://yourserver:6374](http://yourserver:6374)

## Docker

```
git clone https://github.com/JCQ81/meshedapp.git
cd meshedapp
docker build -t meshedapp .
docker run -d --name meshedapp \
  -e MESHTASTIC_HOST=192.168.0.1 -p 6374:6374 \
  -v /path/to/store:/opt/meshedapp/store meshedapp
```

## Synology NAS

This guide has _only_ been tested on DiskStation Manager v7.1.1-42962

- Download the source as .zip, unpack it and upload the directory to your NAS
- From a terminal, run:

```
cd /path/to/meshedapp
python3 -m venv ./env
source ./env/bin/activate
python3 -m ensurepip
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade meshtastic flask waitress
python3 ./meshedapp.py [meshtastic-device-ip]
```

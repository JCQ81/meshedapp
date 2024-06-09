# MeshedApp

A simple web interface for your Meshtastic chat centrally hosted on your home server. 

![](./img/example1.png)

## Setup

```
git clone https://github.com/JCQ81/meshedapp.git
cd meshedapp
./meshedapp.py [meshedapp-ip]
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

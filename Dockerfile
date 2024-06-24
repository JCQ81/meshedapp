FROM    alpine:3.20

RUN     apk add --no-cache tzdata bash git python3

RUN     mkdir -p /opt/meshedapp && cd /opt/meshedapp \
        && python3 -m venv ./env \
        && source ./env/bin/activate \        
        && python3 -m ensurepip \
        && python3 -m pip install --upgrade pip \
        && python3 -m pip install --upgrade meshtastic flask waitress \
        && deactivate

# RUN     adduser -u 6374 -D meshedapp; echo meshedapp:$(cat /dev/urandom | base64 | head -c 12) | chpasswd \
#         && git clone https://github.com/JCQ81/meshedapp.git /opt/meshedapp \
#         && cd /opt/meshedapp && /bin/bash -O extglob -c 'chown -R meshedapp !("env")'

ADD     web /opt/meshedapp/web
ADD     data /opt/meshedapp/data
ADD     meshedapp.py /opt/meshedapp/meshedapp.py
RUN     adduser -u 6374 -D meshedapp; echo meshedapp:$(cat /dev/urandom | base64 | head -c 12) | chpasswd \
        && cd /opt/meshedapp && /bin/bash -O extglob -c 'chown -R meshedapp !("env")'

ADD     docker-entrypoint.sh /docker-entrypoint.sh
CMD     ["/docker-entrypoint.sh"]

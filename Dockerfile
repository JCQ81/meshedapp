FROM    alpine:3.20

RUN     apk add --no-cache bash git python3

# RUN     adduser -u 6374 -D meshedapp; echo meshedapp:$(cat /dev/urandom | base64 | head -c 12) | chpasswd \
#         && git clone https://github.com/JCQ81/meshedapp.git /opt/meshedapp \
#         && chown -R meshedapp /opt/meshedapp

ADD     meshedapp.py /opt/meshedapp/meshedapp.py
ADD     web /opt/meshedapp/web
RUN     adduser -u 6374 -D meshedapp; echo meshedapp:$(cat /dev/urandom | base64 | head -c 12) | chpasswd \
        && chown -R meshedapp /opt/meshedapp

RUN     cd /opt/meshedapp \
        && python3 -m venv ./env \
        && source ./env/bin/activate \        
        && python3 -m ensurepip \
        && python3 -m pip install --upgrade pip \
        && python3 -m pip install --upgrade meshtastic flask waitress \
        && deactivate

ADD     docker-entrypoint.sh /docker-entrypoint.sh
CMD     ["/docker-entrypoint.sh"]

FROM    almalinux:9

RUN     dnf -y install epel-release \
        && dnf -y update && dnf -y upgrade \
        && dnf -y install python3 python3-flask python3-pip \ 
        && pip install meshtastic \
        && yum clean all

ADD     meshedapp.py /opt/meshedapp/meshedapp.py
ADD     web /opt/meshedapp/web

ADD     docker-entrypoint.sh /docker-entrypoint.sh
CMD     ["/docker-entrypoint.sh"]

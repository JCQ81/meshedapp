#!/bin/bash

PTH=/opt/meshedapp
if [ ! -f $PTH/store/_all.csv ]; then
  mkdir -p $PTH/store
  echo "Initial load;;Welcome in your Meshtastic primary channel" >$PTH/store/_all.csv
fi
chown -R meshedapp:meshedapp $PTH/store
chmod -R 644 $PTH/store/*

if [ -z $MESHTASTIC_HOST ]; then
  su - meshedapp -c "cd $PTH; export TZ=$TZ; source ./env/bin/activate && python3 ./meshedapp.py" 2>/dev/null
else
  su - meshedapp -c "cd $PTH; export TZ=$TZ; source ./env/bin/activate && python3 ./meshedapp.py $MESHTASTIC_HOST" 2>/dev/null
fi

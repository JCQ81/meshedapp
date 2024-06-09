#!/bin/bash

cd /opt/meshedapp
if [ ! -f ./store/_all.csv ]; then
  mkdir -p ./store
  echo "Initial load;;Welcome in your Meshtastic primary channel" >./store/_all.csv
fi

if [ -z ${MESHTASTIC_HOST} ]; then
  ./meshedapp.py
else
  ./meshedapp.py ${MESHTASTIC_HOST}
fi

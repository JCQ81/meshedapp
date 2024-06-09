#!/usr/bin/python3

import time, os, sys, datetime, meshtastic, meshtastic.serial_interface, meshtastic.tcp_interface
from flask import Flask, Response, json, request, abort
from pubsub import pub

#### == Globals == ####

self = None
nodes = {}
ltime = time.time()
interface = None

app = Flask(__name__)

def init():
  global self
  global interface
  pub.subscribe(onReceive, "meshtastic.receive.text")
  if len(sys.argv) < 2:
    interface = meshtastic.serial_interface.SerialInterface()
  else:
    interface = meshtastic.tcp_interface.TCPInterface(hostname=sys.argv[1])
  self = f'!{str(hex(interface.myInfo.my_node_num))[2:]}'
  for id,data in interface.nodes.items():
    nodes[id] = data['user'] 

def onReceive(packet, interface): # called when a packet arrives
  global ltime
  ltime = time.time()
  sender = packet['fromId']
  filenm = '_all' if packet['toId'] == '^all' else packet['fromId'][1:]
  text = packet['decoded']['text'].replace('\n', ' ').replace('\r', '')
  f = open(f'store/{filenm}.csv', 'a')
  f.write(f"{datetime.datetime.fromtimestamp(packet['rxTime']).strftime('%Y-%m-%d %H:%M:%S')};{sender};{text}\n")
  f.close()

def httpfile(target):
  if target in ['index.html', 'index.css', 'index.js', 'index.json', 'jquery-3.6.0.min.js' ]:
    file = open(f'./web/{target}', 'r')
    data = file.read()
    file.close()
    return Response(data, mimetype='text/' + target[::-1].split('.')[0][::-1])
  else:
    abort(404)   

#### == Flask Routes == ####

# Default
@app.route('/', methods=['GET'])
def rt_rtt():
  return httpfile('index.html')

# Web content
@app.route('/<path:target>', methods=['GET'])
def rt_def(target):
  return httpfile(target)

# Status
@app.route('/msh/status', methods=['GET'])
def rt_status_get():
  global ltime
  return Response(json.dumps({ 'update':int(ltime) }), mimetype='application/json')

# Node list
@app.route('/msh/nodes', methods=['GET'])
def rt_nodes_get():
  global nodes
  lmsg = {}
  path = './store'
  for filenm in [item for item in os.listdir(path) if os.path.isfile(f'{path}/{item}')]:
    file = open(f'{path}/{filenm}', 'r')
    data = file.readlines()
    file.close()
    lmsg[f'!{filenm[:-4]}'] = str(data[-1].split(';')[2].rstrip('\n'))
  return Response(json.dumps({ 'nodes':nodes, 'lmsg':lmsg }), mimetype='application/json')

# Node data
@app.route('/msh/<node>', methods=['GET'])
def rt_msh_get(node):
  file = open(f'./store/{node}.csv', 'r')
  data = file.read()
  file.close()
  return Response(data, mimetype='text/plain')

# Node send
@app.route('/msh/<node>', methods=['POST'])
def rt_msh_post(node):
  global ltime
  global interface
  msg = request.get_json(force=True)['msg']
  if node == '_all':
    interface.sendText(msg)
  else:
    interface.sendText(msg, f'!{node}')
  f = open(f'store/{node}.csv', 'a')
  f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')};{self};{msg}\n")
  f.close()
  ltime = time.time()
  return Response('')  

#### == Main == ####
if __name__ == '__main__':
  init()
  print('Connected')
  app.run(host='0.0.0.0', port=6374)

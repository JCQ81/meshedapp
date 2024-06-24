#!/usr/bin/python3

import time, os, sys, datetime, meshtastic, meshtastic.serial_interface, meshtastic.tcp_interface
from flask import Flask, Response, json, request, send_file, abort
from threading import Thread
from waitress import serve
from pubsub import pub

#### == Globals == ####

myId = None
nodes = {}
ltime = time.time()
interface = None

app = Flask(__name__)

# Initialize connection, gather info
def init():
  global myId
  global nodes
  global interface
  pub.subscribe(onReceive, "meshtastic.receive.text")
  pub.subscribe(onDisconnect, "meshtastic.connection.lost")
  if len(sys.argv) < 2:
    interface = meshtastic.serial_interface.SerialInterface()
  else:
    interface = meshtastic.tcp_interface.TCPInterface(hostname=sys.argv[1])
  print('Connected')
  myId = f'!{str(hex(interface.myInfo.my_node_num))[2:]}'
  for id,data in interface.nodes.items():
    nodes[id] = data['user']

# Flush stdout for docker logs
def bgFlush():
  while True:
    time.sleep(1)
    sys.stdout.flush()

# Auto reconnect every 30min for restoring connection on any uncatchable error 
# ( interface.close() triggers onDisconnect() )
def bgRefresh():
  global interface
  while True:
    time.sleep(1800)
    print('Refresh: ', end='')
    interface.close()

# Recieve packet
def onReceive(packet, interface):
  global ltime
  ltime = time.time()
  sender = packet['fromId']
  filenm = '_all' if packet['toId'] == '^all' else packet['fromId'][1:]
  text = packet['decoded']['text'].replace('\n', ' ').replace('\r', '')
  f = open(f'store/{filenm}.csv', 'a')
  f.write(f"{datetime.datetime.fromtimestamp(packet['rxTime']).strftime('%Y-%m-%d %H:%M:%S')};{sender};{text}\n")
  f.close()

# Auto reconnect on disconnect
def onDisconnect(interface):
  print('Reconnecting... ', end='')
  init()

# Return files from ./web
def httpfile(target):
  if target in ['index.html', 'index.css', 'index.js', 'index.json', 'jquery-3.6.0.min.js', 'favicon.ico' ]:
    if target == 'favicon.ico':
      return send_file(f'./web/{target}', mimetype='image/gif')
    else:
      return send_file(f'./web/{target}', mimetype='text/' + target[::-1].split('.')[0][::-1])
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
  if os.path.isfile(f'./store/{node}.csv'):
    file = open(f'./store/{node}.csv', 'r')
    data = file.read()
    file.close()
    return send_file(f'./store/{node}.csv', mimetype='text/plain')
  else:
    return Response('', mimetype='text/plain')

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
  f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')};{myId};{msg}\n")
  f.close()
  ltime = time.time()
  return Response('')  

#### == Main == ####
if __name__ == '__main__':
  os.umask(18)
  init()
  Thread(target=bgFlush, daemon=True, name='bgFlush').start()
  Thread(target=bgRefresh, daemon=True, name='bgRefresh').start()
  serve(app, host="0.0.0.0", port=6374)

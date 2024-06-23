#!/usr/bin/python3

import time, os, sys, datetime, random, threading, traceback
import meshtastic, meshtastic.serial_interface, meshtastic.tcp_interface
from flask import Flask, Response, json, request, send_file, abort
from threading import Thread
from waitress import serve
from pubsub import pub

#### == Globals == ####

myId = None
nodes = {}
channels = {}
lpack = {}
ltime = time.time()
ltracelen = 0
interface = None
rssfeed = None

app = Flask(__name__)

# Initialize connection, gather info
def init():
  global myId
  global nodes
  global channels
  global interface
  # Setup Meshtastic 
  pub.subscribe(onReceive, "meshtastic.receive.text")
  pub.subscribe(onDisconnect, "meshtastic.connection.lost")
  if len(sys.argv) < 2:
    interface = meshtastic.serial_interface.SerialInterface()
  else:
    interface = meshtastic.tcp_interface.TCPInterface(hostname=sys.argv[1])
  log('Connected')
  # Fill up buffers
  myId = f'!{str(hex(interface.myInfo.my_node_num))[2:]}'
  for id,data in interface.nodes.items():
    nodes[id] = data['user']
  for channel in interface.getNode('^local').channels:
    if channel.role != 0:
      channels[str(channel.index)] = channel.settings.name

# sendText wrapper with reconnect
def sendText(msg, dst='^all', channelIndex=0):
  global interface
  retry = 4
  while retry > 0:
    try:
      interface.sendText(msg, dst, channelIndex=channelIndex)
      return True
    except:
      retry -= 1
      interface.close()
      time.sleep(10)
  print("Message not sent!!! (ノಠ益ಠ)ノ彡┻━┻")

# Flush stdout for docker logs
def bgFlush():
  while True:
    time.sleep(1)
    sys.stdout.flush()

# Auto reconnect every 30min for restoring connection on any uncatchable error 
# ( interface.close() triggers onDisconnect() )
def bgRefresh():
  global nodes
  global interface
  global ltracelen
  rcnt = 0
  while True:
    time.sleep(120)
    rcnt += 1
    # Gather traceinfo
    stacktrace = ""
    for th in threading.enumerate():
      stacktrace += str(th)
      stacktrace += "".join(traceback.format_stack(sys._current_frames()[th.ident]))
    ntracelen = len(stacktrace)
    # Reconnect on trace detection
    if ltracelen < ntracelen:
      log(f'TraceData: {stacktrace[ltracelen:]}')
      log(f'DataLength: {ntracelen}')      
      ltracelen = ntracelen
      interface.close()
    # Reconnect every 30min anyway
    elif rcnt >= 15:
      rcnt = 0
      interface.close()

# Recieve packet
def onReceive(packet, interface):
  global myId
  global nodes
  global ltime  
  global lpack
  # Debug for detecting emtpy source
  if packet['fromId'] == None:
    log('Packet with NoneType fromId: ')
    pprint(packet)
  # Set Id's
  sender = packet['fromId']
  filenm = packet['fromId'][1:]
  # Determine store file
  if packet['decoded']['text'].startswith('/'):
    filenm = '_cmd'
  if packet['toId'] == '^all':
    if 'channel' in packet:
      channel = str(packet['channel'])
      filenm = f'_ch{channel}'
    else:
      filenm = '_all'
  # Prepare data
  text = packet['decoded']['text'].replace('\n', ' ').replace('\r', '')
  ltime = time.time()
  if ( sender != myId ):
    lpack = { 'sender':f'!{filenm}', 'text':text }
  store = open(f'store/{filenm}.csv', 'a')
  store.write(f"{datetime.datetime.fromtimestamp(packet['rxTime']).strftime('%Y-%m-%d %H:%M:%S')};{sender};{text}\n")
  # Process commands
  if filenm == '_cmd':
    time.sleep(1)
    # /ping
    if text.lower() == ('/ping'):      
      sendText('...pong', sender)
      store.write(f"{datetime.datetime.fromtimestamp(packet['rxTime']).strftime('%Y-%m-%d %H:%M:%S')};{myId};Pong\n")
    # /pong
    if text.lower() == ('/pong'):      
      sendText('/ping', sender)
      store.write(f"{datetime.datetime.fromtimestamp(packet['rxTime']).strftime('%Y-%m-%d %H:%M:%S')};{myId};/ping\n")
    # /echo
    if text.lower().startswith('/echo'):
      sendText(text[6:], sender)
      store.write(f"{datetime.datetime.fromtimestamp(packet['rxTime']).strftime('%Y-%m-%d %H:%M:%S')};{myId};{text[6:]}\n")
    # /joke
    if text.lower().startswith('/joke'):
      with open('data/joke.txt', 'r') as jokes:
        joke = random.choice(jokes.read().splitlines())
      sendText(joke, sender)
      store.write(f"{datetime.datetime.fromtimestamp(packet['rxTime']).strftime('%Y-%m-%d %H:%M:%S')};{myId};{joke}\n")
  # Generate RSS feed (if not a command)
  else:
    sender = nodes[sender]['shortName']+' | '+nodes[sender]['longName'] if sender in nodes else sender
    genfeed(sender, text)
  store.close()

# Auto reconnect on disconnect
def onDisconnect(interface):
  log('Reconnecting... ')
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

# Prepare RSS feed
def genfeed(sender=None, text=None):
  global rssfeed
  with open('data/rss.xml') as f:
    rssbody = f.read()
  pubdate = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z").strip()
  rssitem = "" 
  if sender != None:
    rssitem = "<item><title>%sender</title><description>%text</description><pubDate>%pubdate</pubDate></item>".replace('%sender', sender).replace('%text', text).replace('%pubdate', pubdate)
  rssfeed = rssbody.replace('%pubdate', pubdate).replace('%item', rssitem)

# Log.... :)
def log(msg):
  print(f'[{datetime.datetime.now()}] {msg}')

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
  global lpack
  retval = { 'update':int(ltime) } if not lpack else { 'update':int(ltime), 'sender':lpack['sender'], 'message':lpack['text'] }
  lpack = {}
  return Response(json.dumps(retval), mimetype='application/json')

# Node list
@app.route('/msh/nodes', methods=['GET'])
def rt_nodes_get():
  global nodes
  global channels
  lmsg = {}
  path = './store'
  for filenm in [item for item in os.listdir(path) if os.path.isfile(f'{path}/{item}')]:
    with open(f'{path}/{filenm}', 'r') as store:
      data = store.readlines()
    lmsg[f'!{filenm[:-4]}'] = str(data[-1].split(';')[2].rstrip('\n'))
  return Response(json.dumps({ 'nodes':nodes, 'channels':channels, 'lmsg':lmsg }), mimetype='application/json')

# Node data
@app.route('/msh/<node>', methods=['GET'])
def rt_msh_get(node):
  if os.path.isfile(f'./store/{node}.csv'):
    with open(f'./store/{node}.csv', 'r') as store:
      data = store.readlines()
    return send_file(f'./store/{node}.csv', mimetype='text/plain')
  else:
    return Response('', mimetype='text/plain')

# Node send
@app.route('/msh/<node>', methods=['POST'])
def rt_msh_post(node):
  global ltime
  global interface
  msg = request.get_json(force=True)['msg']
  if node.startswith('_'):
    if node == '_all':
      sendText(msg)
    else:
      sendText(msg, '^all', channelIndex=int(node[-1]))
  else:
    sendText(msg, f'!{node}')
  with open(f'store/{node}.csv', 'a') as store:
    store.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')};{myId};{msg}\n")
  ltime = time.time()
  return Response('')

# Node send
@app.route('/rss', methods=['GET'])
def rt_rss_get():
  global rssfeed
  if rssfeed == None:
    genfeed()
  return Response(rssfeed, mimetype='application/rss+xml')

#### == Main == ####
if __name__ == '__main__':
  os.umask(18)
  init()
  Thread(target=bgFlush, daemon=True, name='bgFlush').start()
  Thread(target=bgRefresh, daemon=True, name='bgRefresh').start()
  serve(app, host="0.0.0.0", port=6374)

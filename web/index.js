
// Elements
let titlebar = $('<div/>', { class:'titlebar'});
let sidebar = $('<div/>', { class:'sidebar'});
let content = $('<div/>', { class:'content'});
let chatbar = $('<div/>', { class:'chatbar'});
let nodelist = $('<div/>', { class:'nodelist'});
let charcnt = $('<span/>', { class:'chatbar_count' }).html('0');
let version = $('<div/>', { class:'titlebar_version'});
let overlay = $('<div/>', { class:'overlay'});
let popup = $('<div/>', { class:'popup'});
let loader = $('<img/>', { class:'loader', src:'sqbf.gif' });

// Globals
let nodes = {};
let lchange = 0;
let actnode = '!^all';
let chatbox = null;
let chatbtn = null;
let notify = false;

// onLoad
$(document).ready( function () {
  // Check / set notification ability
  if ("Notification" in window) {
    if (Notification.permission === "granted") {
      notify = true;
    }
    else {
      Notification.requestPermission().then(function (permission) {
        if (permission === "granted") {
          notify = true;
        }
      });
    }
  }
  else {
    console.log('Notifications not supported by browser')
  }
  console.log(`Notifications available: ${notify}`);

  // Setup control
  let control = $('<div/>', { class:'titlebar_control'}).append(
    $('<img/>', { class:'titlebar_control_img', src:'icrfr.png'}).on('click', function() {
      location.reload();
    }),
    $('<img/>', { class:'titlebar_control_img', src:'icrss.png'}).on('click', function() {
      window.open('./rss', '_blank');
    }),
    $('<img/>', { class:'titlebar_control_img', src:'icpwr.png'}).on('click', function() {
      overlay.show();
    }),
  );

  // Power cycle popup
  let pctarget = $('<select/>', {  }).append(
    $('<option>', { value:0, text:'None'}),
    $('<option>', { value:1, text:'Meshtastic Device'}),
    $('<option>', { value:2, text:'MeshedApp Backend'}),
    $('<option>', { value:3, text:'Both'})
  );
  popup.append(
    'Please select your target for power cycle:<br/>',
    pctarget,
    $('<input/>', { class:'popup_button', type:'button', style:'right:200px;' })
      .val('Apply')
      .on('click', function() {
        let reload = 0;
        if (pctarget.val() == 1) {
          if (confirm('This will reboot your Meshtastic device, are you sure?')) {
            reload += 20000;
          }
        }
        if (pctarget.val() > 1) {
          if (confirm('This will shutdown your MeshedApp Backend.\n\n!! Note that MeshedApp will become unavailable if no restart mechanic is in place.\n\nAre you sure you want to continue?')) {
            if (confirm('MeshedApp may become unavailabe.\n\nAre you really really sure???')) {
              reload += 15000;
            }
          }          
        }
        if (reload == 0) {
          overlay.hide();
        }
        else {
          api('post', 'power', {state:pctarget.val()});
          popup.hide();
          loader.show();
          setInterval(function() {
            location.reload();
          }, reload);
        }
      }),
    $('<input/>', { class:'popup_button', type:'button' })
      .val('Cancel')
      .on('click', function() { 
        overlay.hide();
      }) 
  )

  // Page base
  let link = $('<img/>', { src:'iclnk.png', class:'titlebar_link'}).on('click', function() {
    window.open('https://github.com/JCQ81/meshedapp', '_blank');
  })
  $('body').append(
    titlebar
      .text('MeshedApp')
      .append(link)
      .append(version)
      .append(control), 
    sidebar, 
    content, 
    chatbar, 
    nodelist, 
    overlay
      .append(loader, popup)
  );

  // Chat input bar
  chatbox = $('<input/>', { class:'chatbar_input', style:'width:640px;', maxlength:235 })
    .on('keydown', function(event) {
      if (event.which == '13') { 
        sendChat(actnode, $(this).val());
      }
    }).on('change input keyup cut copy paste', function() {
      charcnt.html(this.value.length);
    });
  chatbtn = $('<input/>', { class:'chatbar_button', type:'button' })
    .val('✉')
    .on('click', function() { 
      sendChat(actnode, chatbox.val());
    });
  chatbar.append(chatbox, charcnt, chatbtn);

  // (Auto-) update
  update();
  setInterval(() => { update(); }, 2000);
});

// global default onclick
$(document).on('click', function(event) {
  if (event.target.className != 'sidebar_add') {
    nodelist.hide();
  }
});

// Update page content
function update() {
  $.when( api('get', 'status') ).done(function(status) {
    if (status.update != lchange) {
      $.when( api('get', 'nodes') ).done(function(data) {
        // Update globals and UI
        nodes = data;
        version.text(`v${data.server.version}`);
        loadNav();
        loadChat(actnode);
        // Send notification
        if (notify && lchange != 0 && 'sender' in status && !status.message.startsWith('/')) {
          let sender = (status.sender in nodes.nodes) ? nodes.nodes[status.sender].shortName : 'Unknown User'
          let ntfc = new Notification(`${sender}: ${status.message}`);
        }
        lchange = status.update;
      });
    }        
  });
}

// Generate node element
function genNode(id, shortName, longName, msg='') {  
  msg = (msg.length > 20) ? msg.trim().substring(0,24) + '...' : msg;  
  longName = (longName.length > 20) ? longName.trim().substring(0,14) + '...' : longName;
  nodeColor = (id.startsWith('!_')) ? 'ccc' : strColor(id);
  let node = $('<div/>', { class:'sidebar_node'}).append(
    $('<div/>', { class:'node_shortname', style:`background:#${nodeColor}`}).text(shortName),
    $('<div/>', { class:'node_longname'}).text(longName),
    $('<div/>', { class:'node_text'}).text(msg)
  ).on('click', function() {
    loadChat(id);
  });
  return node;

}

// Set navigation element
function loadNav() {  
  sidebar.empty();
  // New chat/node
  sidebar.append(
    $('<div/>', { class:'sidebar_add'}).text('👤➕')
      .on('click', function() {
        nodelist.empty().show();
        $.each(nodes.nodes, function(id, nodeInfo) {          
          let nodecolor = strColor(id);
          let newnode = [
            $('<div/>', { class:'node_shortname', style:`background:#${nodecolor}`}).text(nodeInfo.shortName),
            $('<div/>', { class:'node_longname'}).text(nodeInfo.longName),
            $('<div/>', { class:'node_text'}).text()
          ]         
          nodelist.append(
            $('<div/>', { class:'sidebar_node'}).append(
              newnode
            ).on('click', function() {
              if (!nodes.lmsg[id]) {
                content.empty();
                sidebar.append(
                  $('<div/>', { class:'sidebar_node'}).append(
                    newnode
                  ).on('click', function() {
                    content.empty();
                    loadChat(id);
                  })
                );
              }
              loadChat(id);
              nodelist.hide();
            })
          )
        })
      })
  );
  let inner = $('<div/>', { class:'sidebar_inner' });
  sidebar.append(inner);
  // Add channels
  $.each(nodes.channels, function(cid, cname) {
    let id = (cid == '0') ? '!_all' : `!_ch${cid}`;
    inner.append(
      genNode(
        id,
        `CH${cid}`,
        (cname == '') ? `Channel ${cid}` : cname,
        (id in nodes.lmsg) ? nodes.lmsg[id] : ''
      )
    );
  });
  // Add nodes
  $.each(nodes.lmsg, function(id, msg) {
    if (!id.startsWith('!_')) {
      if (id in nodes.nodes) {
        inner.append(
          genNode(
            id,
            nodes.nodes[id].shortName,
            nodes.nodes[id].longName,
            msg
          )
        );
      }
      else {
        inner.append(
          genNode(
            id,
            '[----]',
            id,
            msg
          )
        );
      }
    }
  });
  // Add CMD log
  inner.append(
    genNode('!_cmd', 'CMD', '/CMD', ('!_cmd' in nodes.lmsg) ? nodes.lmsg['!_cmd'] : '' )
  );
}

// Load active conversation
function loadChat(node) {
  actnode = node;
  node = (node == '!^all') ? '_all' : node.slice(1);
  $.when( api('get', node) ).done(function(data) {
    let lines = data.split('\n');
    let inner = $('<div/>', { class:'content_inner' });
    // Load chat lines
    content.empty().append(inner);
    for (let i=0; i<lines.length; i++) {
      if (lines[i].length > 3) {
        // Format line
        let line = lines[i].split(';');
        let lmsg = line.slice(2).join(';').replace(/(<([^>]+)>)/ig, '');
        let shnm = (typeof line[1] == 'undefined' || typeof nodes.nodes[line[1]] == 'undefined') ? line[1] : nodes.nodes[line[1]].shortName;
        let nodecolor = (typeof line[1] == 'undefined') ? 'CCC' :strColor(line[1]);
        let words = lmsg.split(/[\s,]+/);
        words.forEach(function(word) {
          if (word.match(/^(ht|f)tp/) && word.match(/(ht|f)tp[s]?\:\/\/[a-zA-Z0-9\-\.\:@]+([a-zA-Z0-9\/\:\.\-_?=&#%]*)?$/)) {
            lmsg = lmsg.replace(word, `<a href="${word}" target=_blank>${word}</a>`);
          }          
        });
        // Display line
        inner.append(
          $('<div/>', { class:'content_message'}).append(
            $('<div/>', { class:'node_shortname', style:`background:#${nodecolor}`}).text(shnm),
            $('<div/>', { class:'msg_text'}).html(lmsg),
            $('<div/>', { class:'msg_time'}).text(line[0])
          )
        );
      }
    }
    content.scrollTop(inner.height());
  });
  // Set chat input status
  if (node == '_cmd') {
    chatbox.attr('disabled','disabled');
    chatbtn.attr('disabled','disabled');
  }
  else {
    chatbox.removeAttr('disabled');
    chatbtn.removeAttr('disabled');
    chatbox.focus();
  }  
}

// Post mew message
function sendChat(node, msg) {
  node = (node == '!^all') ? '_all' : node.slice(1);
  $.when( 
    api('post', node, {msg:msg})
  ).fail(function() {
    alert('Error sending message');    
  }).done(function() {
    chatbox.val('');
    update();
  });
}

// Global API call
function api(httpmethod, path, data) {
  let xhr = $.ajax({
    url: `msh/${path}`,
    type: httpmethod,
    data: JSON.stringify(data),
    error: function (response) { },
    success: function (response, status, xhr) { }
  });
  return xhr;
}

// Generate color based on string
function strColor(str) {
  let hash = 0;
  for (var i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  let c = (hash & 0x00FFFFFF).toString(16).toUpperCase();
  return "00000".substring(0, 6 - c.length) + c;
}

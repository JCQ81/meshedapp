
let titlebar = $('<div/>', { class:'titlebar'});
let sidebar = $('<div/>', { class:'sidebar'});
let content = $('<div/>', { class:'content'});
let chatbar = $('<div/>', { class:'chatbar'});
let nodelist = $('<div/>', { class:'nodelist'});

let nodes = {};
let lchange = 0;
let actnode = '!^all';
let chatbox = null;

$(document).ready( function () {
  $('body').append(titlebar.text('MeshedApp'), sidebar, content, chatbar, nodelist);
  chatbox = $('<input/>', { class:'chatbar_input' })
    .on('keydown', function(event) { 
      if (event.which == '13') { 
        sendChat(actnode, $(this).val());
      } 
    });
  chatbar.append(
    chatbox, '&emsp;',
    $('<input/>', { class:'chatbar_button', type:'button' })
      .val('✉')
      .on('click', function() { 
        sendChat(actnode, chatbox.val());
      })
  );
  update();
  setInterval(() => { update(); }, 2000);
});

// global default onclick
$(document).on('click', function(event) {
  if (event.target.className != 'sidebar_add') {
    nodelist.hide();
  }
});

function update() {
  $.when( api('get', 'status') ).done(function(status) {
    if (status.update != lchange) {
      $.when( api('get', 'nodes') ).done(function(data) {
        nodes = data;
        loadNav();
        loadChat(actnode);
        lchange = status.update;
      });
    }        
  });
}

function loadNav() {
  sidebar.empty().append(
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
  $.each(nodes.lmsg, function(id, msg) {
    let longName = 'Channel 0';
    let shortName = '0';   
    let nodecolor = 'ccc';
    msg = (msg.length > 20) ? msg.trim().substring(0,20) + '...' : msg;
    if (id != '!_all') {
      shortName = nodes.nodes[id].shortName;
      longName = nodes.nodes[id].longName;
      nodecolor = strColor(id);
    }    
    sidebar.append(
      $('<div/>', { class:'sidebar_node'}).append(
        $('<div/>', { class:'node_shortname', style:`background:#${nodecolor}`}).text(shortName),
        $('<div/>', { class:'node_longname'}).text(longName),
        $('<div/>', { class:'node_text'}).text(msg)
      ).on('click', function() {
        loadChat(id);
      }),
    );
  });  
}

function loadChat(node) {
  actnode = node;
  node = (node == '!^all') ? '_all' : node.slice(1);
  $.when( api('get', node) ).done(function(data) {
    let lines = data.split('\n');
    let inner = $('<div/>');
    content.empty().append(inner);
    for (let i=0; i<lines.length; i++) {
      if (lines[i].length > 3) {
        let line = lines[i].split(';',3);
        let shnm = (typeof line[1] == 'undefined' || typeof nodes.nodes[line[1]] == 'undefined') ? line[1] : nodes.nodes[line[1]].shortName;
        let nodecolor = (typeof line[1] == 'undefined') ? 'CCC' :strColor(line[1]);
        inner.append(
          $('<div/>', { class:'content_message'}).append(
            $('<div/>', { class:'node_shortname', style:`background:#${nodecolor}`}).text(shnm),
            $('<div/>', { class:'msg_text'}).text(line[2]),
            $('<div/>', { class:'msg_time'}).text(line[0])
          )
        );
      }
    }
    content.scrollTop(inner.height());
  });
  chatbox.focus();
}

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

function strColor(str) {
  let hash = 0;
  for (var i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  let c = (hash & 0x00FFFFFF).toString(16).toUpperCase();
  return "00000".substring(0, 6 - c.length) + c;
}

/*jslint browser:true, esnext:true*/

var update_timeout;
let last_update = 0;

const UPDATE_INTERVAL = 1000 * 60 * 15;

function update(data) {

  //console.log(data);
  var w = data.weather.state;
  var temp = w.main.temp;
  var icon = w.weather[0].icon;
  var sensor = data['sensor 1'];
  var depth = sensor.depth;
  var volume = sensor.volume;
  var pump = data['pump 1'];
  var pump_state = pump.state;

  const options = {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
    second: 'numeric'
  };
  let message_time = new Date(data.message_time).toLocaleString('en-GB',
    options);

  document.getElementById('icon').src = '/static/img/' + icon + '.png';
  document.getElementById('temp').innerText = temp + ' °C';
  document.getElementById('depth').innerText = depth + ' mm';
  document.getElementById('volume').innerText = volume + ' litres';
  document.getElementById('pump_state').innerText = 'Pump ' + pump_state;
  document.getElementById('message_time').innerText = message_time;

}

function show_json(data) {
  var json = JSON.stringify(data, undefined, 4);
  json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g,
    '&gt;');
  json = json.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    function(match) {
      var cls = 'j_number';
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = 'j_key';
        } else {
          cls = 'j_string';
        }
      } else if (/true|false/.test(match)) {
        cls = 'j_boolean';
      } else if (/null/.test(match)) {
        cls = 'j_null';
      }
      return '<span class="' + cls + '">' + match + '</span>';
    }
  );
  document.getElementById('message_raw').innerHTML = json;
}


function next_update() {
  var now = new Date().getTime();
  if (now - last_update >= UPDATE_INTERVAL) {
    return 0;
  }
  return UPDATE_INTERVAL - now % UPDATE_INTERVAL;
}

function request(url, callback, payload) {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', url, true);
  xhr.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      callback(JSON.parse(this.responseText), payload);
    }
  };
  xhr.send();
}

function update_status() {
  if (update_timeout) {
    clearTimeout(update_timeout);
  }
  request('/status', update);

  last_update = new Date().getTime();
  update_timeout = setTimeout(update_status, next_update());
}

document.onvisibilitychange = () => {
  if (document.visibilityState === 'hidden') {
    if (update_timeout) {
      clearTimeout(update_timeout);
    }

  } else {

    update_timeout = setTimeout(update_status, next_update());
  }
};
document.getElementById('main').addEventListener('click', update_status);

function make_value(value, col_info) {
  if (col_info.type === 'date') {
    value = new Date(value).toLocaleDateString();
  }

  if (col_info.type === 'time') {
    value = value.substring(0, 5);
  }

  if (col_info.type === 'float') {
    value = value.toFixed(2);
  }

  if (col_info.type === 'seconds') {
    var minutes = Math.floor(value / 60);
    var seconds = value - minutes * 60;
    value = '' + minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
  }

  if (col_info.units) {
    value += ' ' + col_info.units;
  }
  return value;

}


function update_stats(data) {
  const cols = data.cols;
  const values = data.values;
  let table = document.createElement('table');
  let thead = document.createElement('thead');
  table.appendChild(thead);
  let tr = document.createElement('tr');
  thead.appendChild(tr);
  for (const col of cols) {
    let th = document.createElement('th');
    th.innerText = col.title;
    th.setAttribute('class', col.type);
    tr.appendChild(th);
  }
  let tbody = document.createElement('tbody');
  table.appendChild(tbody);
  values.forEach(row => {
    let tr = document.createElement('tr');
    tbody.appendChild(tr);
    for (let i = 0; i < cols.length; i++) {
      let value = make_value(row[i], cols[i]);
      let td = document.createElement('td');
      td.setAttribute('class', cols[i].type);
      td.innerText = value;
      tr.appendChild(td);
    }

  });

  document.body.appendChild(table);
}

function stats() {
  request('/stats', update_stats);
  request('/stats_pump', update_stats);
  request('/stats_weather', update_stats);
}

update_status();
stats();

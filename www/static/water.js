/*jslint browser:true, esnext:true*/

var update_timeout;
let last_update = 0;

const LOCALE = 'en-GB';
const UPDATE_INTERVAL = 1000 * 60 * 15;

function update(data) {

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
  let message_time = new Date(data.message_time).toLocaleString(LOCALE,
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


function next_update() {
  var now = new Date().getTime();
  if (now - last_update >= UPDATE_INTERVAL) {
    return 0;
  }
  return UPDATE_INTERVAL - now % UPDATE_INTERVAL;
}


function update_status() {
  if (update_timeout) {
    clearTimeout(update_timeout);
  }
  request('/status', update);
  last_update = new Date().getTime();
  update_timeout = setTimeout(update_status, next_update());
}

function make_value(value, col_info) {
  if (col_info.type === 'date') {
    const options = {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    };
    value = new Date(value).toLocaleString(LOCALE, options);
  }

  if (col_info.type === 'time') {
    value = value.substring(0, 5);
  }

  if (col_info.type === 'float') {
    value = value.toFixed(1);
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


function show_selected_table() {
  let selected_option = document.querySelector('span.option.selected');
  if (selected_option === null) {
    return;
  }

  let selected = selected_option.dataset.select;

  document.querySelectorAll('table').forEach(el => {
    if (el.dataset.name === selected) {
      el.style.display = 'table';
    } else {
      el.style.display = 'none';
    }
  });
}

function update_stats(data, stat) {
  let table = create_table(data);
  table.dataset.name = stat;
  table.style.display = 'none';
  document.getElementById('tables').appendChild(table);
  show_selected_table();
  document.querySelector('[data-select=' + stat + ']').style.display = 'inline-block';
}

function create_table(data) {
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
  return table;
}

function option_select(event) {
  document.querySelectorAll('span.option').forEach(el => el.classList.remove('selected'));
  event.target.classList.add('selected');
  show_selected_table();
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
document.querySelectorAll('span.option').forEach(el => el.addEventListener('click', option_select));

function init() {
  update_status();
  request('/stats_depth', update_stats, 'depth');
  request('/stats_volume', update_stats, 'volume');
  request('/stats_pump', update_stats, 'pump');
  request('/stats_weather', update_stats, 'weather');
}

init();

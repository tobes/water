/*jslint browser:true, esnext:true*/

var update_timeout;
let last_update = 0;
let data_cache = {};
const LOCALE = 'en-GB';
const UPDATE_INTERVAL = 1000 * 60 * 15;

function update(data, automated) {

  var w = data.weather.state;
  var temp = w.main.temp;
  var icon = w.weather[0].icon;
  var sensor = data['sensor 1'];
  var depth = sensor.depth;
  var volume = sensor.volume;
  var accuracy = sensor.accuracy;
  var pump = data['pump 1'];
  var pump_state = pump.state;
  var msg_time = data.message_time;

  var accuracy_text;

  if (accuracy === 0) {
    accuracy_text = 'excellent';
  } else if (accuracy < 0.5) {
    accuracy_text = 'good';
  } else if (accuracy < 2) {
    accuracy_text = 'adaquate';
  } else if (accuracy < 4) {
    accuracy_text = 'poor';
  } else {
    accuracy_text = 'awful';
  }
  const options_date = {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  };
  let message_date = new Date(msg_time).toLocaleString(LOCALE, options_date);

  const options_time = {
    hour: 'numeric',
    minute: 'numeric',
    second: 'numeric'
  };

  let message_time = new Date(msg_time).toLocaleString(LOCALE, options_time);

  document.getElementById('weather_icon').src = '/static/img/' + icon + '.png';
  document.getElementById('temp').innerText = temp;
  document.getElementById('depth').innerText = depth;
  document.getElementById('volume').innerText = volume;
  document.getElementById('accuracy').innerText = accuracy_text + ' accuracy';
  document.getElementById('accuracy').className = accuracy_text;
  document.getElementById('pump_state').innerText = 'Pump ' + pump_state;
  document.getElementById('message_time').innerText = message_time;
  document.getElementById('message_date').innerText = message_date;

  document.getElementById('loading').style.display = 'none';
  document.getElementById('main_info').style.display = 'block';

  if (automated === true) {
    request('/stats', update_stats);
  }
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
  url = 'https://tollington.duckdns.org/' + url;
  //url = 'http://192.168.1.7:5000/' + url;
  var xhr = new XMLHttpRequest();
  xhr.open('GET', url, true);
  xhr.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      if (this.responseText) {
        callback(JSON.parse(this.responseText), payload);
      }
    }
  };
  xhr.send();
}

function jlog(value) {
  console.log(JSON.stringify(value, undefined, 4))
}

function random_int(max) {
  return Math.floor(Math.random() * (Math.floor(max) + 1));
}

function next_update() {
  var now = new Date().getTime();
  if (now - last_update >= UPDATE_INTERVAL) {
    return 0;
  }
  let delay = UPDATE_INTERVAL - now % UPDATE_INTERVAL;
  delay += random_int(UPDATE_INTERVAL * 0.01)
  if (delay < 5000) {
    delay = 5000
  }
  return delay;
}


function update_status(automated) {
  if (automated !== true){
    document.getElementById('accuracy').innerText = 'updating';
    document.getElementById('accuracy').className = 'updating';
  }
  if (update_timeout) {
    clearTimeout(update_timeout);
  }
  request('/status', update, automated);
  last_update = new Date().getTime();
  update_timeout = setTimeout(update_status, next_update(), true);
}

function yyyymmddToLocalDate(isoString) {
  const [year, month, day] = isoString.split('-');
  return new Date(year, month - 1, day);
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
    value = display_seconds(value);
  }

  return value;
}

function display_seconds(value) {
  var minutes = Math.floor(value / 60);
  var seconds = value - minutes * 60;
  return '' + minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
}

function show_selected_table() {
  let selected_option = document.querySelector('li.option.selected');
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

  document.querySelectorAll('canvas').forEach(el => el.style.display = 'none');
}



function show_selected() {

  let selected_option = document.querySelector('[data-type=stat].selected');
  let selected_display = document.querySelector('[data-type=display].selected');
  let selected_period = document.querySelector('[data-type=period].selected');
  if (selected_option === null || selected_display === null || selected_period === null) {
    return;
  }

  let stat = selected_option.dataset.value;
  let display = selected_display.dataset.value;
  let period = selected_period.dataset.value;

  let cutoff = cut_off_date(period);

  const data = data_cache[stat];

  let values = [];

  if (data) {
    data.values.forEach(row => {
      if (yyyymmddToLocalDate(row[0]) > cutoff) {
        values.push(row);
      }
    });
    if (values.length === 0) {
      display = 'no data';
    }
  } else {
    display = 'unknown';
  }

  let el;
  switch (display) {
    case 'graph':
      el = document.createElement('div');
      el.appendChild(create_graph(data.graph, data.cols, values, cutoff));
      break;
    case 'table':
      el = create_table(data.cols, values);
      break;
    case 'no data':
      el = document.createElement('div');
      el.id = 'data_error';
      el.innerText = 'No data available for this date range.';
      break;
    case 'unknown':
      el = document.createElement('div');
      el.id = 'data_error';
      el.innerText = 'Sorry not available';
      break;
  }
  update_stat_display(el);
}

function update_stat_display(content) {
  let data_div = document.getElementById('data')
  data_div.appendChild(content);
  graph_resize();
  let child_nodes = data_div.childNodes.forEach(el => {
    if (el !== content) {
      el.remove();
    }
  });
}

function cut_off_date(days) {
  var d = new Date();
  d.setDate(d.getDate() - days);
  d.setHours(0, 0, 0, 0);
  return d;
}

function create_graph(graph, cols, values, cutoff) {
  let scales = {
    x: {
      type: 'time',
      time: {
        unit: 'day'
      },
      min: new Date(cutoff - 1),
      max: new Date().setHours(0, 0, 0, 0)
    }
  }

  for (const key in graph.axis) {
    if (!scales[key]) {
      scales[key] = {};
    }
    Object.assign(scales[key], graph.axis[key]);
  }

  let col_index = {}
  for (let i = 0; i < cols.length; i++) {
    col_index[cols[i].title] = i;
  }

  let chart_data = [];

  for (const key in graph.dataset) {
    let dataset = {
      data: [],
      label: key,
      yAxisID: 'y'
    };
    Object.assign(dataset, graph.dataset[key] || {});
    let index = col_index[key];
    values.forEach(row => {
      let date = new Date(row[0]);
      dataset.data.push({
        x: date,
        y: row[index]
      });
    });
    chart_data.push(dataset)
  }

  let chart_ = {
    type: 'line',
    options: {
      animation: false,
      maintainAspectRatio: false,
      scales: scales,
      elements: {
        point: {
          radius: 0
        },
        line: {
          borderWidth: 2
        }
      },
      plugins: {
        tooltip: {
          enabled: false
        },
        legend: {
          labels: {
            font: {
              size: 15
            }
          }
        }
      }
    }
  }

  // any tick callback functions
  let fn;
  for (const key in scales) {
    if (scales[key].tick_units) {
      if (!scales[key].ticks) {
        scales[key].ticks = {};
      }
      if (scales[key].tick_units === 'seconds') {
        fn = (value, index, ticks) => display_seconds(value);
      } else {
        fn = (value, index, ticks) => value + scales[key].tick_units;
      }
      scales[key].ticks.callback = fn;
    }
  }
  Object.assign(chart_.options.scales, scales);


  chart_['data'] = {
    'datasets': chart_data
  };


  const canvas = document.createElement('canvas');
  new Chart(canvas, chart_);
  return canvas;
}

function graph_resize() {
  let size;

  let w = window.innerWidth;
  let h = window.innerHeight;

  let ratio = 1.25;

  if (h < w) {
    size = Math.floor(w / ratio);
  } else {
    size = Math.floor(w * ratio);
  }
  size = Math.min(size, h)

  document.querySelectorAll('canvas').forEach(el => {
    el.parentNode.style.height = size + 'px';
  });
}

function update_stats(data) {

  data.forEach(row => {
    let name = row.name;
    data_cache[name] = row.data;
    if (document.querySelector('[data-value=' + name + ']') === null) {
      let button = document.createElement('li');
      button.dataset.type = 'stat';
      button.dataset.value = name;
      button.innerText = name;
      if (document.querySelectorAll('#options li').length === 0) {
        button.classList.add('selected');
      }
      button.addEventListener('click', button_select);
      document.getElementById('options').appendChild(button);
    }
  });
  document.getElementById('visualization').style.display = 'block';
  const options_date = {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
  };

  let message_time = new Date().toLocaleString(LOCALE, options_date);
  document.getElementById('data_update_time').innerText = 'Updated: ' + message_time;
  show_selected();
}

function create_table(cols, values) {

  let table = document.createElement('table');
  let thead = document.createElement('thead');
  table.appendChild(thead);
  let tr = document.createElement('tr');
  thead.appendChild(tr);
  for (const col of cols) {
    let th = document.createElement('th');
    th.innerText = col.title;
    th.setAttribute('class', col.type);
    if (col.units) {
      let units = document.createElement('span');
      units.innerText = col.units;
      units.classList.add('units');
      th.append(units);
    }
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
  //table.dataset.name = stat;
  return table;
}

function button_select(event) {
  let type = event.target.dataset.type;
  document.querySelectorAll('[data-type=' + type + ']').forEach(
    el => el.classList.remove('selected')
  );
  event.target.classList.add('selected');
  show_selected();
}

function move_scroll_top() {
  let el = document.getElementById('scroll_top');
  if (window.scrollY < 50) {
    el.style.display = 'none';
  } else {
    el.style.display = 'block';
  }
}

function scroll_top() {
  if ('scrollBehavior' in document.documentElement.style) {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  } else {
    window.scrollTo(0, 0);
  }
}

document.onvisibilitychange = () => {
  if (document.visibilityState === 'hidden') {
    if (update_timeout) {
      clearTimeout(update_timeout);
    }
  } else {
    update_timeout = setTimeout(update_status, next_update(), true);
  }
};

function init() {
  scroll_top();
  update_status(true);
}

window.addEventListener('load', init);
document.addEventListener('scroll', move_scroll_top);
//window.addEventListener('resize', graph_resize);

document.getElementById('scroll_top').addEventListener('click', scroll_top);
document.getElementById('main_info').addEventListener('click', update_status);

document.querySelectorAll('li').forEach(
  el => el.addEventListener('click', button_select)
);

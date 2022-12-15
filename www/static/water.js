/*jslint browser:true, esnext:true*/

var update_timeout;
let last_update = 0;
let data_cache = {};
let offline = true;
const LOCALE = 'en-GB';
const UPDATE_INTERVAL = 1000 * 60 * 15;
const OFF_LINE_CHECK = 1000 * 5;

function update(data, automated) {

  let stale = stale_time(data);
  if (stale) {
    document.getElementById('stale_status_msg').innerText = 'OFFLINE: Status ' + stale + ' old';
    document.getElementById('stale_status').style.display = 'block';
    offline = true;
  } else {
    document.getElementById('stale_status').style.display = 'none';
    offline = false;
  }

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
  document.getElementById('temp').innerText = temp.toFixed(1);
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


function request(url, callback, payload) {
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
  const interval = (offline ? OFF_LINE_CHECK :UPDATE_INTERVAL);
  let delay = interval - now % interval;
  //delay += random_int(interval * 0.01)
  if (delay < 5000) {
    delay = 5000
  }
  return delay;
}


function update_status(automated, first) {
  if (automated !== true) {
    document.getElementById('accuracy').innerText = 'updating';
    document.getElementById('accuracy').className = 'updating';
  }
  if (update_timeout) {
    clearTimeout(update_timeout);
  }
  let url = '/status';
  if (first) {
    url += '?fast';
  }
  request(url, update, automated);
  last_update = new Date().getTime();
  set_update_timer();
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
  let min_date = new Date(cutoff)
  min_date.setHours(0, 0, 0, 0);
  min_date.setDate(min_date.getDate() + 1);

  let max_date = new Date()
  max_date.setHours(0, 0, 0, 0)

  let scales = {
    x: {
      type: 'time',
      time: {
        unit: 'day'
      },
      min: min_date,
      max: max_date
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


function seconds_2_nice(seconds) {

  let day = Math.floor(seconds / 86400);
  if (day) {
    return day + (day === 1 ? ' day' : ' days');
  }

  let parts = new Date(seconds * 1000).toISOString().substr(11, 8).split(':');
  let hour = parseInt(parts[0]);
  let min = parseInt(parts[1]);
  let sec = parseInt(parts[2]);

  if (hour) {
    return hour + (hour === 1 ? ' hour' : ' hours');
  }
  if (min) {
    return min + (min === 1 ? ' minute' : ' minutes');
  }
  return sec + (sec === 1 ? ' second' : ' seconds');
}

function stale_time(data) {

  let data_epoch = data.epoch_time;
  let current_epoch = new Date() / 1000;

  let difference = current_epoch - data_epoch;
  if (difference < 5) {
    return;
  }
  return seconds_2_nice(Math.floor(difference));

}

function update_stats(data) {

  let stale = stale_time(data);
  if (stale) {
    document.getElementById('stale_stats_msg').innerText = 'OFFLINE: Data ' + stale + ' old';
    document.getElementById('stale_stats').style.display = 'block';
  } else {
    document.getElementById('stale_stats').style.display = 'none';
  }

  data.data.forEach(row => {
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
    set_update_timer();
  }
};


function set_update_timer() {
  if (update_timeout) {
    return;
  }
  update_timeout = setTimeout(update_status, next_update(), true);
}


function init() {
  scroll_top();
  update_status(true, true);
}

window.addEventListener('load', init);
document.addEventListener('scroll', move_scroll_top);
//window.addEventListener('resize', graph_resize);

document.getElementById('scroll_top').addEventListener('click', scroll_top);
document.getElementById('main_info').addEventListener('click', update_status);

document.querySelectorAll('li').forEach(
  el => el.addEventListener('click', button_select)
);

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js', {'scope':'https://tollington.duckdns.org/'});
}

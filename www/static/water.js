'use strict';

const LOCALE = 'en-GB';

// how often to update status (seconds)
const UPDATE_INTERVAL_STATUS = 60 * 5;

// how often to update stats (seconds);
const UPDATE_INTERVAL_STATS = 60 * 60;

// if offline check if online every (seconds)
const OFF_LINE_CHECK = 60;

const STATS_DATE_OPTIONS = {
  weekday: 'long',
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  hour: 'numeric',
  minute: 'numeric'
};

const STATUS_DATE_OPTIONS = {
  weekday: 'long',
  year: 'numeric',
  month: 'long',
  day: 'numeric',
};

const STATUS_TIME_OPTIONS = {
  hour: 'numeric',
  minute: 'numeric',
  second: 'numeric'
};

const TABLE_DATE_OPTIONS = {
  weekday: 'short',
  month: 'short',
  day: 'numeric',
};


const STATE = {
  status_timeout: null,
  stats_timeout: null,
  status_last_data: null,
  stats_last_data: null,
  status_due_time: null,
  stats_due_time: 0,
  data_cache: {},
  offline: true
};


function datetime_format(datetime, format_options) {
  // format datetime in locale using options
  return new Date(datetime).toLocaleString(LOCALE, format_options);
}


function accuracy_2_text(accuracy) {
  // convert an accuracy score to english
  if (accuracy === 0) {
    return 'excellent';
  }
  if (accuracy < 0.5) {
    return 'good';
  }
  if (accuracy < 2) {
    return 'adaquate';
  }
  if (accuracy < 4) {
    return 'poor';
  }
  return 'awful';
}


function set_element_text(id, text) {
  // set elements text
  const el = document.getElementById(id);
  if (el) {
    el.innerText = text;
  } else {
    console.log('element id `' + id + '` not found');
  }
}


function set_element_display(id, display) {
  // set elements display style 'block' or 'none'
  const el = document.getElementById(id);
  if (el) {
    el.style.display = (display ? 'block' : 'none');
  } else {
    console.log('element id `' + id + '` not found');
  }
}


function update_status_display(data, automated) {
  // update the status infomation shown

  const stale = stale_time(data, UPDATE_INTERVAL_STATUS);
  set_element_text('stale_status_msg', 'Status ' + stale + ' old');
  set_element_display('stale_status', stale);
  STATE.offline = Boolean(stale);

  if (data === undefined) {
    return;
  }
  STATE.status_last_data = data.epoch_time * 1000;
  const w = data.weather.state;
  const pump = data['pump 1'];
  const sensor = data['sensor 1'];

  update_accuracy_text(accuracy_2_text(sensor.accuracy), ' accuracy');

  set_element_text('temp', w.main.temp.toFixed(1));
  set_element_text('depth', sensor.depth);
  set_element_text('volume', sensor.volume);
  set_element_text('pump_state', 'Pump ' + pump.state);

  const msg_time = data.message_time;
  set_element_text('message_time', datetime_format(msg_time, STATUS_TIME_OPTIONS));
  set_element_text('message_date', datetime_format(msg_time, STATUS_DATE_OPTIONS));

  const icon = w.weather[0].icon;
  document.getElementById('weather_icon').src = '/static/img/' + icon + '.png';
  set_element_display('loading', false);
  set_element_display('main_info', true);
}


function make_http_request(url, callback, payload) {
  const xhr = new XMLHttpRequest();
  xhr.open('GET', url, true);
  xhr.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      if (this.responseText) {
        callback(JSON.parse(this.responseText), payload);
      }
    }
  };
  xhr.onerror = () => {
    STATE.offline = true;
    callback();
  };
  xhr.send();
}


function update_accuracy_text(text, post_fix = '') {
  set_element_text('accuracy', text + post_fix);
  document.getElementById('accuracy').className = text;
}


function update_status(automated, first) {

  clear_status_timeout();

  // user feedback on update
  if (automated !== true) {
    update_accuracy_text('updating');
  }

  make_http_request('/status', update_status_display, automated);

  set_status_timeout();
  // see if stats need updating
  if (!STATE.offline) {
    set_stats_timeout();
  }
}


function update_stats() {
  // get stats
  make_http_request('/stats', update_stats_callback);
  set_stats_timeout();
}


function yyyymmddToLocalDate(isoString) {
  const [year, month, day] = isoString.split('-');
  return new Date(year, month - 1, day);
}


function make_table_value(value, col_info) {
  switch (col_info.type) {
    case 'date':
      return datetime_format(value, TABLE_DATE_OPTIONS);
    case 'time':
      return value.substring(0, 5);
    case 'float':
      return value.toFixed(1);
    case 'seconds':
      return display_seconds(value);
  }
  return value;
}


function display_seconds(value) {
  const minutes = Math.floor(value / 60);
  const seconds = value - minutes * 60;
  return '' + minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
}


function get_option(option) {
  // get option value
  const selected_option = document.querySelector('[data-type=' + option + '].selected');
  return selected_option.dataset.value;
}


function show_selected() {

  let display = get_option('display');
  const cutoff = cut_off_date(get_option('period'));
  const data = STATE.data_cache[get_option('stat')];

  // build our values
  const values = [];
  if (data) {
    data.values.forEach(row => {
      if (display !== 'table' || yyyymmddToLocalDate(row[0]) > cutoff) {
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

  const data_div = document.getElementById('data');
  // remove existing stat
  data_div.childNodes.forEach(el => el.remove());
  // add new
  data_div.appendChild(el);
  graph_resize();
}


function cut_off_date(days) {
  // create date starting days ago
  // for limiting data and graph axis
  const d = new Date();
  d.setDate(d.getDate() - days);
  d.setHours(0, 0, 0, 0);
  return d;
}


function build_chart_data(scales, datasets) {
  return {
    type: 'line',
    data: {
      datasets: datasets
    },
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
  };
}


function create_axis(axis, cutoff, limits) {
  const min_date = new Date(cutoff);
  min_date.setHours(0, 0, 0, 0);
  min_date.setDate(min_date.getDate() + 1);

  const max_date = new Date();
  max_date.setHours(0, 0, 0, 0);

  // create axis
  const scales = {
    x: {
      type: 'time',
      time: {
        unit: 'day'
      },
      min: min_date,
      max: max_date
    }
  };

  // merge in our axis
  for (const key in axis) {
    if (!scales[key]) {
      scales[key] = {};
    }
    if (limits[key]) {
      scales[key].suggestedMax = limits[key].max;
      scales[key].suggestedMin = limits[key].min;
    }
    Object.assign(scales[key], axis[key]);
  }

  // any tick callback functions
  for (const key in scales) {
    if (scales[key].tick_units) {
      let fn;
      if (!scales[key].ticks) {
        scales[key].ticks = {};
      }
      if (scales[key].tick_units === 'seconds') {
        fn = display_seconds;
      } else {
        fn = (value, index, ticks) => value + scales[key].tick_units;
      }
      scales[key].ticks.callback = fn;
    }
  }
  return scales;
}


function create_graph(graph, cols, values, cutoff) {
  // get column index for each data
  const col_index = {};
  for (let i = 0; i < cols.length; i++) {
    col_index[cols[i].title] = i;
  }

  // build datasets
  const chart_data = [];
  const limits = {};
  for (const key in graph.dataset) {
    const dataset = {
      data: [],
      label: key,
      yAxisID: 'y'
    };
    // merge our data set info
    Object.assign(dataset, graph.dataset[key] || {});

    // build chart data
    const index = col_index[key];
    let max = 0;
    let min = 0;
    const yAxisID = dataset.yAxisID;
    if (limits[yAxisID] === undefined) {
      limits[yAxisID] = {
        max: 0,
        min: 0
      };
    }
    for (let i = 0; i < values.length; i++) {
      let row = values[i];
      // date is always first column in data
      const date = new Date(row[0]);
      dataset.data.push({
        x: date,
        y: row[index]
      });
      max = Math.max(row[index], max);
      min = Math.min(row[index], min);
    }
    limits[yAxisID].max = Math.max(limits[yAxisID].max, max);
    limits[yAxisID].min = Math.min(limits[yAxisID].min, min);
    chart_data.push(dataset);
  }
  const axis = create_axis(graph.axis, cutoff, limits);
  const chart_ = build_chart_data(axis, chart_data);

  const canvas = document.createElement('canvas');

  new Chart(canvas, chart_);
  return canvas;
}


function graph_resize() {
  // resize graph
  let size;

  const w = window.innerWidth;
  const h = window.innerHeight;

  const ratio = 1.25;

  if (h < w) {
    size = Math.floor(w / ratio);
  } else {
    size = Math.floor(w * ratio);
  }
  size = Math.min(size, h);

  // graph container resizer triggers resize
  const el = document.querySelector('canvas');
  if (el) {
    el.parentNode.style.height = size + 'px';
  }
}


function seconds_2_nice(seconds) {
  // human friendly time period eg '5 minutes'

  function build(value, unit) {
    if (unit !== 1) {
      unit += 's';
    }
    return value + ' ' + unit;
  }

  const day = Math.floor(seconds / 86400);
  if (day) {
    return build(day, 'day');
  }

  const parts = new Date(seconds * 1000).toISOString().substr(11, 8).split(':');
  const hour = parseInt(parts[0]);
  const min = parseInt(parts[1]);
  const sec = parseInt(parts[2]);

  if (hour) {
    return build(hour, 'hour');
  }
  if (min) {
    return build(min, 'minute');
  }
  return build(sec, 'second');
}


function stale_time(data, limit) {

  // check if our data is stale
  if (data === undefined) {
    return ' ';
  }
  const difference = (Date.now() / 1000) - data.epoch_time;
  if (difference < limit) {
    return;
  }
  return seconds_2_nice(Math.floor(difference));
}


function build_button(group, name) {
  // create buttons if missing
  if (document.querySelector('[data-value=' + name + ']') === null) {
    const button = document.createElement('li');
    button.dataset.type = 'stat';
    button.dataset.value = name;
    button.innerText = name;

    const button_group = document.getElementById(group);
    // first button selected
    if (button_group.childNodes.length === 0) {
      button.classList.add('selected');
    }
    button.addEventListener('click', option_button_click);
    button_group.appendChild(button);
  }
}


function update_stats_callback(data) {

  // show if stale data
  const stale = stale_time(data, UPDATE_INTERVAL_STATS);
  set_element_text('stale_stats_msg', 'Data ' + stale + ' old');
  set_element_display('stale_stats', stale);

  if (data === undefined) {
    return;
  }

  STATE.stats_last_data = data.epoch_time * 1000;

  // process data
  data.data.forEach(row => {
    const name = row.name;
    // save the stat data
    STATE.data_cache[name] = row.data;
    build_button('options', name);
  });

  set_element_display('visualization', true);

  const message_time = datetime_format(Date(), STATS_DATE_OPTIONS);
  set_element_text('data_update_time', 'Updated: ' + message_time);
  show_selected();
}


function create_table(cols, values) {

  const table = document.createElement('table');
  const thead = document.createElement('thead');
  table.appendChild(thead);
  let tr = document.createElement('tr');
  thead.appendChild(tr);
  for (const col of cols) {
    const th = document.createElement('th');
    th.innerText = col.title;
    th.setAttribute('class', col.type);
    if (col.units) {
      const units = document.createElement('span');
      units.innerText = col.units;
      units.classList.add('units');
      th.append(units);
    }
    tr.appendChild(th);
  }
  const tbody = document.createElement('tbody');
  table.appendChild(tbody);
  values.forEach(row => {
    const tr = document.createElement('tr');
    tbody.appendChild(tr);
    for (let i = 0; i < cols.length; i++) {
      const td = document.createElement('td');
      td.setAttribute('class', cols[i].type);
      td.innerText = make_table_value(row[i], cols[i]);
      tr.appendChild(td);
    }
  });
  return table;
}


function option_button_click(event) {
  const type = event.target.dataset.type;
  document.querySelectorAll('[data-type=' + type + ']').forEach(
    el => el.classList.remove('selected')
  );
  event.target.classList.add('selected');
  show_selected();
}


function move_scroll_top() {
  const el = document.getElementById('scroll_top');
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


function clear_status_timeout() {
  if (STATE.status_timeout) {
    clearTimeout(STATE.status_timeout);
  }
}


function timeout_delay(last, max_delay, offline_check) {
  max_delay *= 1000; // ms
  const now = Date.now();
  if (now - last >= max_delay) {
    return 1000;
  }

  if (offline_check && STATE.offline) {
    max_delay = OFF_LINE_CHECK * 1000;
  }
  let delay = max_delay - now % max_delay;
  if (delay < 5000) {
    delay = 5000;
  }
  return delay;
}


function set_status_timeout() {
  clear_status_timeout();
  const last = STATE.status_last_data;
  const delay = timeout_delay(last, UPDATE_INTERVAL_STATUS, true);
  if (STATE.status_due_time === null) {
    STATE.status_due_time = Date.now() + delay;
  }
  STATE.status_timeout = setTimeout(update_status, delay, true);
}


function set_stats_timeout() {
  if (STATE.stats_timeout) {
    clearTimeout(STATE.stats_timeout);
  }
  const last = STATE.stats_last_data;
  const delay = timeout_delay(last, UPDATE_INTERVAL_STATS);
  STATE.stats_due_time = Date.now() + delay;
  STATE.stats_timeout = setTimeout(update_stats, delay, true);
}


function init() {
  scroll_top();

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js', {
      'scope': 'https://tollington.duckdns.org/'
    });
  }

  update_status(true);
}


window.addEventListener('load', init);
document.addEventListener('scroll', move_scroll_top);
// FIXME do we need this?
//window.addEventListener('resize', graph_resize);

document.getElementById('scroll_top').addEventListener('click', scroll_top);
document.getElementById('main_info').addEventListener('click', update_status);

document.querySelectorAll('li').forEach(
  el => el.addEventListener('click', option_button_click)
);

document.onvisibilitychange = () => {
  if (document.visibilityState === 'hidden') {
    clear_status_timeout();
  } else {
    set_status_timeout();
  }
};



// FIXME unused

function jlog(value) {
  console.log(JSON.stringify(value, undefined, 4));
}


function random_int(max) {
  return Math.floor(Math.random() * (Math.floor(max) + 1));
}

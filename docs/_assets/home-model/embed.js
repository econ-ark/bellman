(() => {
  'use strict';
  const models = {
    housing: {title: 'Housing', file: 'house_choice.bl', example: 'housing-frictions/'},
    pensions: {title: 'Pensions', file: 'retire_choice.bl', example: 'pension-retirement/'},
    'buffer-stock': {title: 'Buffer-stock saving', file: 'buffer_stock.bl', example: 'buffer-stock/buffer_stock/'}
  };
  const requested = new URLSearchParams(location.search).get('model') || 'housing';
  const model = Object.hasOwn(models, requested) ? requested : null;
  const host = document.querySelector('#graph');
  const status = document.querySelector('#loading');
  const statusText = document.querySelector('#loading-text');
  const fallback = document.querySelector('#fallback-link');
  const tabs = [...document.querySelectorAll('[role=tab]')];
  const compact = matchMedia('(max-width:600px)');
  let region = null;
  let initialFit = false;
  let lastSize = '';

  function showFailure(message) {
    status.hidden = false;
    statusText.textContent = message;
    fallback.hidden = false;
  }
  if (!model) {
    document.querySelector('#source-tab').disabled = true;
    showFailure('This model is not available.');
    return;
  }
  document.title = models[model].title + ' · Project Bellman';
  document.querySelector('#filename').textContent = models[model].file;
  fallback.href = '../../examples/' + models[model].example;
  fallback.textContent = 'Read about this model';

  function fit() {
    const view = region?.view();
    const frame = host.getBoundingClientRect();
    if (!view?.viewport || !frame.width || !frame.height) return;
    const boxes = [...host.querySelectorAll('.react-flow__node, .bf-boundary-label')]
      .map(element => element.getBoundingClientRect()).filter(box => box.width && box.height);
    if (!boxes.length) return;
    const current = view.viewport;
    const left = (Math.min(...boxes.map(box => box.left)) - frame.left - current.x) / current.zoom;
    const top = (Math.min(...boxes.map(box => box.top)) - frame.top - current.y) / current.zoom;
    const right = (Math.max(...boxes.map(box => box.right)) - frame.left - current.x) / current.zoom;
    const bottom = (Math.max(...boxes.map(box => box.bottom)) - frame.top - current.y) / current.zoom;
    const padding = compact.matches ? 16 : 36;
    const zoom = Math.min(1, (frame.width - padding * 2) / (right - left), (frame.height - padding * 2) / (bottom - top));
    if (!Number.isFinite(zoom) || zoom <= 0) return;
    region.setView({viewport: {x: (frame.width - (right - left) * zoom) / 2 - left * zoom, y: (frame.height - (bottom - top) * zoom) / 2 - top * zoom, zoom}, selection: view.selection});
  }
  function selectTab(tab, focus = false) {
    for (const item of tabs) {
      const active = item === tab;
      item.setAttribute('aria-selected', String(active));
      item.tabIndex = active ? 0 : -1;
      document.getElementById(item.getAttribute('aria-controls')).hidden = !active;
    }
    if (focus) tab.focus();
    if (tab.id === 'diagram-tab') requestAnimationFrame(fit);
  }
  for (const tab of tabs) {
    tab.addEventListener('click', () => selectTab(tab));
    tab.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      const index = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (tabs.indexOf(tab) + 1) % tabs.length;
      selectTab(tabs[index], true);
    });
  }

  // Leave ordinary wheel scrolling to the surrounding document.
  host.addEventListener('wheel', event => event.stopImmediatePropagation(), {capture: true, passive: true});
  const resize = new ResizeObserver(() => {
    const size = host.clientWidth + ':' + host.clientHeight;
    if (size !== lastSize && host.clientWidth && host.clientHeight) {
      lastSize = size;
      requestAnimationFrame(fit);
    }
  });
  resize.observe(host);
  async function readJSON(path) {
    const response = await fetch(path);
    if (!response.ok) throw Error('The model could not be loaded.');
    return response.json();
  }
  const sourceStatus = document.querySelector('#source-status');
  readJSON(model + '-source.json').then(source => {
    const excerpt = source.excerpts.forward;
    document.querySelector('#line-range').textContent = 'Lines ' + excerpt.start_line + '–' + excerpt.end_line;
    const code = document.querySelector('#source-code');
    excerpt.text.replace(/\n$/, '').split('\n').forEach((text, index) => {
      const row = document.createElement('span');
      row.className = 'source-line';
      const number = document.createElement('span');
      number.className = 'line-number';
      number.setAttribute('aria-hidden', 'true');
      number.textContent = excerpt.start_line + index;
      row.append(number, document.createTextNode(text));
      code.append(row);
    });
    sourceStatus.hidden = true;
  }).catch(() => {
    sourceStatus.textContent = 'The authored source could not be loaded. ';
    const link = fallback.cloneNode(true);
    link.removeAttribute('id');
    link.hidden = false;
    sourceStatus.append(link);
  });

  Promise.all([
    readJSON(model + '.json'),
    Promise.all([
      document.fonts.load('16px "Archivo"'),
      document.fonts.load('16px "IBM Plex Mono"'),
      document.fonts.load('500 16px "IBM Plex Mono"'),
      document.fonts.load('16px "STIX Two Math"', '𝑉≻∘')
    ]).catch(() => { throw Error('The diagram fonts could not be loaded.'); })
  ]).then(([data]) => {
    if (!window.BellmanFlow) throw Error('The diagram renderer could not be loaded.');
    // Narrow frames start collapsed; resizing preserves the reader's opened layers.
    region = window.BellmanFlow.mount(host, {
      ...data, layers: compact.matches ? [] : data.layers, scope: model + '-homepage-example',
      controls: () => document.querySelector('#native-controls'),
      processed() {
        status.hidden = true;
        if (!initialFit) {
          initialFit = true;
          requestAnimationFrame(() => requestAnimationFrame(fit));
        }
      },
      refused(info) { showFailure(info.sentence || 'The diagram could not be drawn.'); }
    });
    host.bellmanFlow = region;
  }).catch(error => showFailure(error.message));
  window.addEventListener('pagehide', event => {
    if (!event.persisted) {
      resize.disconnect();
      region?.unmount();
    }
  }, {once: true});
})();

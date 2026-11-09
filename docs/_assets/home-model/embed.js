import {linesForNode} from './source-lines.js?v=20261110p';

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
  const tablist = document.querySelector('.compact-tabs');
  const sourcePanel = document.querySelector('#source-panel');
  const diagramPanel = document.querySelector('#diagram-panel');
  const sourceStatus = document.querySelector('#source-status');
  const kind = document.querySelector('#graph-kind');
  const direction = document.querySelector('#graph-direction');
  const wrap = document.querySelector('#wrap-source');
  const panes = document.querySelector('.pane-layout');
  const resizer = document.querySelector('#pane-resizer');
  const compact = matchMedia('(max-width:759px)');
  const preferenceKey = 'bellman-home-model-view';
  let preferences = {};
  try { preferences = JSON.parse(sessionStorage.getItem(preferenceKey) || '{}') || {}; } catch (_) {}
  if (['initial', 'operator'].includes(preferences.kind)) kind.value = preferences.kind;
  if (['backward', 'forward'].includes(preferences.direction)) direction.value = preferences.direction;
  if (preferences.wrap === false) {
    sourcePanel.dataset.wrap = 'false';
    wrap.setAttribute('aria-pressed', 'false');
  }
  function savePreferences() {
    try { sessionStorage.setItem(preferenceKey, JSON.stringify({kind: kind.value, direction: direction.value, wrap: sourcePanel.dataset.wrap === 'true'})); } catch (_) {}
  }
  let region = null;
  let initialFit = false;
  let lastSize = '';
  let chosenTab = document.querySelector('#diagram-tab');
  let collection = null;
  let currentGraph = '';
  let sourceWidth = 38;
  let sourceLines = [];
  let lastSelection = null;

  function highlightSource(selection) {
    lastSelection = selection;
    const lines = linesForNode(collection, selection, models[model]?.file, sourceLines.length);
    const selected = new Set(lines);
    sourceLines.forEach((row, index) => row.classList.toggle('is-selected', selected.has(index + 1)));
    if (lines.length && !sourcePanel.hidden) {
      const scroll = document.querySelector('.source-scroll');
      const first = sourceLines[lines[0] - 1];
      scroll.scrollTop += first.getBoundingClientRect().top - scroll.getBoundingClientRect().top - 16;
    }
  }

  function showFailure(message) {
    status.hidden = false;
    statusText.textContent = message;
    fallback.hidden = false;
  }
  if (!model) {
    sourceStatus.textContent = 'This model is not available.';
    showFailure('This model is not available.');
  } else {
    document.title = models[model].title + ' · Project Bellman';
    document.querySelector('#filename').textContent = models[model].file;
    document.querySelector('#filename').title = models[model].file;
    fallback.href = '../../examples/' + models[model].example;
    fallback.textContent = 'Read about this model';
  }

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
    chosenTab = tab;
    for (const item of tabs) {
      const active = item === tab;
      item.setAttribute('aria-selected', String(active));
      item.tabIndex = active ? 0 : -1;
      document.getElementById(item.getAttribute('aria-controls')).hidden = compact.matches && !active;
    }
    if (focus) tab.focus();
    if (tab.id === 'diagram-tab') requestAnimationFrame(fit);
    if (tab.id === 'source-tab') highlightSource(lastSelection);
  }
  for (const tab of tabs) {
    tab.addEventListener('click', () => selectTab(tab));
    tab.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      const step = event.key === 'ArrowLeft' ? -1 : 1;
      const index = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (tabs.indexOf(tab) + step + tabs.length) % tabs.length;
      selectTab(tabs[index], true);
    });
  }
  function setPaneLayout() {
    const active = document.activeElement;
    if (compact.matches && sourcePanel.contains(active)) chosenTab = document.querySelector('#source-tab');
    if (compact.matches && diagramPanel.contains(active)) chosenTab = document.querySelector('#diagram-tab');
    tablist.hidden = !compact.matches;
    resizer.hidden = compact.matches;
    for (const panel of [sourcePanel, diagramPanel]) {
      const name = panel === sourcePanel ? 'source' : 'diagram';
      panel.setAttribute('role', compact.matches ? 'tabpanel' : 'region');
      panel.setAttribute('aria-labelledby', name + (compact.matches ? '-tab' : '-heading'));
    }
    selectTab(chosenTab);
    if (!compact.matches && tabs.includes(active)) {
      (active.id === 'diagram-tab' ? kind : document.querySelector('.source-scroll')).focus();
    }
    if (compact.matches && active === resizer) chosenTab.focus();
  }
  setPaneLayout();
  compact.addEventListener('change', setPaneLayout);
  wrap.addEventListener('click', () => {
    const enabled = sourcePanel.dataset.wrap !== 'true';
    sourcePanel.dataset.wrap = String(enabled);
    wrap.setAttribute('aria-pressed', String(enabled));
    savePreferences();
  });

  function resizeSource(pixels) {
    if (compact.matches) return;
    const available = panes.clientWidth - resizer.offsetWidth;
    const width = Math.min(available - 340, Math.max(260, pixels));
    sourceWidth = width / panes.clientWidth * 100;
    panes.style.setProperty('--source-width', sourceWidth + '%');
    resizer.setAttribute('aria-valuemin', String(Math.round(260 / panes.clientWidth * 100)));
    resizer.setAttribute('aria-valuemax', String(Math.round((available - 340) / panes.clientWidth * 100)));
    resizer.setAttribute('aria-valuenow', String(Math.round(sourceWidth)));
    resizer.setAttribute('aria-valuetext', Math.round(width) + ' pixels');
  }
  resizer.addEventListener('pointerdown', event => {
    if (event.button !== 0) return;
    event.preventDefault();
    resizer.focus();
    resizer.setPointerCapture(event.pointerId);
    resizer.dataset.resizing = 'true';
  });
  resizer.addEventListener('pointermove', event => {
    if (resizer.hasPointerCapture(event.pointerId)) resizeSource(event.clientX - panes.getBoundingClientRect().left);
  });
  resizer.addEventListener('pointerup', event => {
    if (resizer.hasPointerCapture(event.pointerId)) resizer.releasePointerCapture(event.pointerId);
  });
  resizer.addEventListener('lostpointercapture', () => { delete resizer.dataset.resizing; });
  resizer.addEventListener('dblclick', () => resizeSource(panes.clientWidth * .38));
  resizer.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const width = sourcePanel.getBoundingClientRect().width;
    resizeSource(event.key === 'Home' ? 260 : event.key === 'End' ? panes.clientWidth : width + (event.key === 'ArrowLeft' ? -24 : 24));
  });

  function graphId() {
    return direction.value + (kind.value === 'initial' ? ' initial diagram' : '');
  }
  function chooseGraph() {
    const graph = graphId();
    if (!collection?.graphs.some(item => item.id === graph)) {
      showFailure('This diagram is not available.');
      return;
    }
    currentGraph = graph;
    highlightSource(null);
    initialFit = false;
    status.hidden = false;
    statusText.textContent = 'Loading the ' + direction.value + ' ' + (kind.value === 'initial' ? 'initial diagram' : 'operator diagram') + '…';
    fallback.hidden = true;
    region.update({graph, select: null});
    savePreferences();
  }
  kind.addEventListener('change', chooseGraph);
  direction.addEventListener('change', chooseGraph);

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
  const paneResize = new ResizeObserver(() => resizeSource(panes.clientWidth * sourceWidth / 100));
  paneResize.observe(panes);
  if (!model) return;
  async function readJSON(path) {
    const response = await fetch(path + new URL(import.meta.url).search);
    if (!response.ok) throw Error('The model could not be loaded.');
    return response.json();
  }
  readJSON(model + '-source.json').then(source => {
    const code = document.querySelector('#source-code');
    source.text.replace(/\n$/, '').split('\n').forEach((text, index) => {
      const row = document.createElement('span');
      row.className = 'source-line';
      const number = document.createElement('span');
      number.className = 'line-number';
      number.setAttribute('aria-hidden', 'true');
      number.textContent = index + 1;
      const content = document.createElement('span');
      content.className = 'line-content';
      content.textContent = text;
      row.append(number, content);
      code.append(row);
      sourceLines.push(row);
    });
    sourceStatus.hidden = true;
    highlightSource(lastSelection);
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
    collection = data.collection;
    currentGraph = graphId();
    region = window.BellmanFlow.mount(host, {
      ...data, graph: currentGraph,
      layers: compact.matches ? Object.fromEntries(Object.keys(data.layers).map(id => [id, []])) : data.layers,
      scope: model + '-homepage-example',
      controls: () => document.querySelector('#native-controls'),
      selected: highlightSource,
      processed(info) {
        if (info.graphId !== currentGraph) return;
        status.hidden = true;
        highlightSource({graphId: info.graphId, nodeId: region?.selection()});
        if (!initialFit) {
          initialFit = true;
          requestAnimationFrame(() => requestAnimationFrame(fit));
        }
      },
      refused(info) { if (info.graphId === currentGraph) showFailure(info.sentence || 'The diagram could not be drawn.'); }
    });
    host.bellmanFlow = region;
    kind.disabled = false;
    direction.disabled = false;
  }).catch(error => showFailure(error.message));
  window.addEventListener('pagehide', event => {
    if (!event.persisted) {
      resize.disconnect();
      paneResize.disconnect();
      compact.removeEventListener('change', setPaneLayout);
      region?.unmount();
    }
  }, {once: true});
})();

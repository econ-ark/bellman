import {linesForNode} from './source-lines.js?v=20261110t';
import {sourceParts} from './source-presentation.js?v=20261110t';

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
  const types = document.querySelector('#source-types');
  const notes = document.querySelector('#source-notes');
  const copy = document.querySelector('#copy-source');
  const copyStatus = document.querySelector('#source-copy-status');
  const panes = document.querySelector('.pane-layout');
  const resizer = document.querySelector('#pane-resizer');
  const compact = matchMedia('(max-width:759px)');
  const bars = [...document.querySelectorAll('.pane-bar')];
  const preferenceKey = 'bellman-home-model-view';
  let preferences = {};
  try { preferences = JSON.parse(sessionStorage.getItem(preferenceKey) || '{}') || {}; } catch (_) {}
  // The Workbench's select (VSCode Elements) takes its choice as its value
  // and as the chosen option's `selected`, which holds before the element
  // is defined.
  function choose(select, value) {
    for (const option of select.querySelectorAll('vscode-option')) option.toggleAttribute('selected', option.getAttribute('value') === value);
    select.value = value;
  }
  if (['initial', 'operator'].includes(preferences.kind)) choose(kind, preferences.kind);
  if (['backward', 'forward'].includes(preferences.direction)) choose(direction, preferences.direction);
  types.setAttribute('aria-pressed', String(preferences.types !== false));
  notes.setAttribute('aria-pressed', String(preferences.notes === true));
  function savePreferences() {
    try { sessionStorage.setItem(preferenceKey, JSON.stringify({
      kind: kind.value, direction: direction.value,
      types: types.getAttribute('aria-pressed') === 'true', notes: notes.getAttribute('aria-pressed') === 'true'
    })); } catch (_) {}
  }
  let region = null;
  let initialFit = false;
  let lastSize = '';
  let chosenTab = document.querySelector('#diagram-tab');
  let collection = null;
  let currentGraph = '';
  // the source pane's share of the frame at first, wide enough at 1440 px for
  // the pane's name, the file's name and the toggles on one row
  const sourceShare = .42;
  let sourceWidth = sourceShare * 100;
  let sourceLines = [];
  let sourceText = [];
  let authoredSource = '';
  let sourceDisplay = null;
  let selectedLines = new Set();
  let lastSelection = null;

  // Each bar keeps one row of 36 px, as the Workbench's graph bar does: where
  // its items do not fit, it hides the file's name first (data-narrow) and
  // then its own name (data-crowded), which stays the pane's heading for
  // assistive technology.
  function measureBars() {
    for (const bar of bars) {
      bar.removeAttribute('data-narrow');
      bar.removeAttribute('data-crowded');
      const overflows = () => bar.scrollWidth > bar.clientWidth + 1;
      if (!overflows()) continue;
      bar.setAttribute('data-narrow', '');
      if (!overflows()) continue;
      bar.setAttribute('data-crowded', '');
    }
  }
  const barResize = new ResizeObserver(measureBars);
  for (const bar of bars) barResize.observe(bar);
  if (document.fonts) document.fonts.ready.then(measureBars);

  function drawSource() {
    const scroll = document.querySelector('.source-scroll');
    const top = scroll.getBoundingClientRect().top;
    const anchor = sourceLines.find(row => row.getBoundingClientRect().bottom > top);
    const offset = anchor ? anchor.getBoundingClientRect().top - top : 0;
    const choices = {types: types.getAttribute('aria-pressed') === 'true', notes: notes.getAttribute('aria-pressed') === 'true'};
    sourceLines.forEach((row, index) => {
      const content = row.querySelector('.line-content');
      const parts = sourceParts(sourceText[index], index + 1, sourceDisplay, choices, selectedLines.has(index + 1));
      content.replaceChildren();
      for (const [partIndex, part] of parts.entries()) {
        if (part.kind === 'text') {
          content.append(document.createTextNode(part.text));
          continue;
        }
        const note = document.createElement('span');
        note.className = 'source-note';
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'source-note-button';
        button.title = part.text.slice(1, -1);
        button.setAttribute('aria-label', 'Show note on line ' + (index + 1) + ': ' + part.text.slice(1, -1));
        button.setAttribute('aria-expanded', 'false');
        const icon = document.createElement('span');
        icon.className = 'codicon codicon-note';
        icon.setAttribute('aria-hidden', 'true');
        button.append(icon);
        const text = document.createElement('span');
        text.className = 'source-note-text';
        text.id = 'source-note-' + index + '-' + partIndex;
        text.textContent = part.text;
        text.hidden = true;
        button.setAttribute('aria-controls', text.id);
        button.addEventListener('click', () => {
          text.hidden = !text.hidden;
          button.setAttribute('aria-expanded', String(!text.hidden));
          button.setAttribute('aria-label', (text.hidden ? 'Show' : 'Hide') + ' note on line ' + (index + 1) + ': ' + part.text.slice(1, -1));
        });
        button.addEventListener('keydown', event => {
          if (event.key !== 'Escape') return;
          text.hidden = true;
          button.setAttribute('aria-expanded', 'false');
          button.setAttribute('aria-label', 'Show note on line ' + (index + 1) + ': ' + part.text.slice(1, -1));
        });
        note.append(button, text);
        content.append(note);
      }
    });
    if (anchor && !sourcePanel.hidden) scroll.scrollTop += anchor.getBoundingClientRect().top - top - offset;
  }

  function highlightSource(selection) {
    lastSelection = selection;
    const lines = linesForNode(collection, selection, models[model]?.file, sourceLines.length);
    const changed = lines.length !== selectedLines.size || lines.some(line => !selectedLines.has(line));
    selectedLines = new Set(lines);
    if (changed) drawSource();
    sourceLines.forEach((row, index) => row.classList.toggle('is-selected', selectedLines.has(index + 1)));
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
    measureBars();
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
    // The drawing whole, at most at scale 1, in the middle of the pane (AAS,
    // 11 November 2026). At least 12 px stay free at its left and at its right
    // and 24 px between the bar and its top. The floating controls and the
    // 12 px under them are left out of the height in which it is centred, and
    // 12 px stay free between it and the controls.
    const controls = document.querySelector('.bl-graph-controls');
    const edge = 12, head = 24, below = (controls?.offsetHeight || 0) + edge;
    const width = right - left, height = bottom - top;
    const zoom = Math.min(1, (frame.width - 2 * edge) / width, (frame.height - head - below - edge) / height);
    if (!Number.isFinite(zoom) || zoom <= 0) return;
    const x = Math.round((frame.width - width * zoom) / 2 - left * zoom);
    const y = Math.round(Math.max(head, (frame.height - below - height * zoom) / 2) - top * zoom);
    region.setView({viewport: {x, y, zoom}, selection: view.selection});
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
    measureBars();
    if (!compact.matches && tabs.includes(active)) {
      (active.id === 'diagram-tab' ? kind : document.querySelector('.source-scroll')).focus();
    }
    if (compact.matches && active === resizer) chosenTab.focus();
  }
  setPaneLayout();
  compact.addEventListener('change', setPaneLayout);
  for (const control of [types, notes]) {
    control.addEventListener('click', () => {
      control.setAttribute('aria-pressed', String(control.getAttribute('aria-pressed') !== 'true'));
      drawSource();
      savePreferences();
    });
  }
  copy.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(authoredSource);
      copyStatus.textContent = 'Complete source copied.';
      copy.title = 'Complete source copied';
    } catch (_) {
      copyStatus.textContent = 'Copy failed. Show types and notes, then select the source to copy it.';
      copy.title = 'Copy failed. Show types and notes, then select the source to copy it.';
    }
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
  resizer.addEventListener('dblclick', () => resizeSource(panes.clientWidth * sourceShare));
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
    authoredSource = source.text;
    sourceText = source.text.replace(/\n$/, '').split('\n');
    sourceDisplay = source.display;
    sourceText.forEach((text, index) => {
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
    const hasDisplay = Array.isArray(sourceDisplay?.types) && Array.isArray(sourceDisplay?.notes);
    types.disabled = !hasDisplay || sourceDisplay.types.length === 0;
    notes.disabled = !hasDisplay || sourceDisplay.notes.length === 0;
    if (hasDisplay && !sourceDisplay.notes.length) notes.title = 'This model has no annotation notes';
    sourceStatus.hidden = true;
    copy.disabled = false;
    drawSource();
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
      barResize.disconnect();
      compact.removeEventListener('change', setPaneLayout);
      region?.unmount();
    }
  }, {once: true});
})();

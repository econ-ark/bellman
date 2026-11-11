(() => {
  'use strict';
  const home = document.querySelector('.bellman-home');
  if (!home) return;
  import('./home-module-wires.js').then(({drawModuleWires}) => drawModuleWires(home));

  const modelTabs = [...home.querySelectorAll('[data-model]')];
  const modelFrame = home.querySelector('#home-model-frame');
  // The frame's scripts weigh more than the page; they load when the Applications section arrives.
  function loadFrame() {
    if (!modelFrame.getAttribute('src') && modelFrame.dataset.src) modelFrame.src = modelFrame.dataset.src;
  }
  if ('IntersectionObserver' in window) {
    new IntersectionObserver((entries, observer) => {
      if (entries.some(entry => entry.isIntersecting)) { loadFrame(); observer.disconnect(); }
    }, {rootMargin: '240px 0px'}).observe(home.querySelector('#home-model-panel'));
  } else loadFrame();
  function selectModel(tab, focus = false) {
    if (tab.getAttribute('aria-selected') !== 'true') {
      const model = tab.dataset.model;
      const loaded = Boolean(modelFrame.getAttribute('src'));
      const url = new URL(loaded ? modelFrame.src : modelFrame.dataset.src, location.href);
      url.searchParams.set('model', model);
      if (loaded) modelFrame.contentWindow.location.replace(url.href);
      else modelFrame.dataset.src = url.href;
      history.replaceState({...history.state, bellmanModel: model}, '');
      modelFrame.title = tab.textContent + ' model: interactive diagram and source';
      home.querySelector('#home-model-panel').setAttribute('aria-labelledby', tab.id);
      modelTabs.forEach(item => {
        const active = item === tab;
        item.setAttribute('aria-selected', String(active));
        item.tabIndex = active ? 0 : -1;
      });
    }
    if (focus) tab.focus();
  }
  modelTabs.forEach(tab => {
    tab.addEventListener('click', () => selectModel(tab));
    tab.addEventListener('keydown', event => {
      // The tabs are a row on a wide window and a column on a narrow one, so both pairs of arrow keys move between them.
      const step = {ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1}[event.key];
      if (!step && !['Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? modelTabs.length - 1
        : (modelTabs.indexOf(tab) + step + modelTabs.length) % modelTabs.length;
      selectModel(modelTabs[next], true);
    });
  });

  function restoreModel() {
    const saved = modelTabs.find(tab => tab.dataset.model === history.state?.bellmanModel);
    if (saved) selectModel(saved);
  }
  restoreModel();
  addEventListener('pageshow', restoreModel);
  home.querySelector('.home-model-tabs').hidden = false;

  const media = home.querySelector('[data-home-media]');
  if (!media || !('IntersectionObserver' in window)) return;
  const preference = matchMedia('(prefers-reduced-motion: reduce)');
  const scenes = [...media.querySelectorAll('[data-scene]')];
  const pause = media.querySelector('.home-media__pause');
  const night = media.querySelector('[data-home-night]');
  const date = media.querySelector('time');
  const firstYear = Number(date.dateTime);
  const lastYear = 2023;
  let selected = 0;
  let visible = false;
  let scrolling = false;
  let userPaused = false;
  let paused = preference.matches;
  let rotation = null;
  let requestedYear = null;
  let imageRequest = 0;

  function running() {
    return visible && !paused && !document.hidden;
  }
  function isNight() {
    return scenes[selected].dataset.scene === 'night';
  }
  function cancelYear() {
    ++imageRequest;
    requestedYear = null;
  }
  async function showYear(year) {
    if (year === requestedYear) return;
    if (year === Number(date.dateTime)) {
      if (requestedYear !== null) cancelYear();
      return;
    }
    const request = ++imageRequest;
    requestedYear = year;
    const image = new Image();
    image.src = new URL(year + '.jpg', night.src).href;
    try {
      await image.decode();
      if (request !== imageRequest || !running() || !isNight()) return;
      night.src = image.src;
      date.dateTime = date.textContent = String(year);
      requestedYear = null;
    } catch {
      if (request === imageRequest) requestedYear = null;
    }
  }
  function updateYear() {
    if (!running() || !isNight()) return;
    const bounds = media.getBoundingClientRect();
    if (bounds.bottom <= 0 || bounds.top >= innerHeight) return;
    const progress = Math.max(0, Math.min(1, -bounds.top / Math.max(1, bounds.height * .4)));
    showYear(firstYear + Math.round(progress * (lastYear - firstYear)));
  }
  function updatePlayback() {
    const active = running();
    scenes.forEach((scene, index) => {
      if (scene.tagName !== 'VIDEO') return;
      if (active && !scrolling && index === selected) {
        if (!scene.hasAttribute('src')) scene.src = scene.dataset.src;
        scene.play().catch(() => {});
      } else scene.pause();
    });
    pause.textContent = paused ? 'Play' : 'Pause';
    pause.setAttribute('aria-label', paused ? 'Play background animation' : 'Pause background animation');
    if (!active) {
      clearTimeout(rotation);
      rotation = null;
      cancelYear();
      return;
    }
    updateYear();
    if (rotation === null) {
      rotation = setTimeout(() => {
        rotation = null;
        selectScene((selected + 1) % scenes.length);
      }, isNight() ? 16000 : 10000);
    }
  }
  function selectScene(index) {
    cancelYear();
    selected = index;
    scenes.forEach((scene, i) => { scene.hidden = i !== index; });
    media.querySelector('[data-home-year]').hidden = !isNight();
    updatePlayback();
  }
  pause.addEventListener('click', () => { userPaused = paused = !paused; updatePlayback(); });
  preference.addEventListener('change', event => { paused = event.matches || userPaused; updatePlayback(); });
  document.addEventListener('visibilitychange', updatePlayback);
  pause.hidden = false;
  new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    updatePlayback();
  }, {threshold: 0}).observe(media);

  let scrollCheck = false;
  let scrollIdle = null;
  function checkScroll() {
    scrollCheck = false;
    const bounds = media.getBoundingClientRect();
    if (bounds.bottom <= 0 || bounds.top >= innerHeight) return;
    clearTimeout(scrollIdle);
    if (!scrolling) {
      scrolling = true;
      updatePlayback();
    } else updateYear();
    scrollIdle = setTimeout(() => {
      scrolling = false;
      updatePlayback();
    }, 160);
  }
  function scheduleScrollCheck() {
    if (scrollCheck) return;
    scrollCheck = true;
    requestAnimationFrame(checkScroll);
  }
  addEventListener('scroll', scheduleScrollCheck, {passive: true});
  addEventListener('resize', scheduleScrollCheck);
  updatePlayback();
})();

/* Navigation-only shell. Hide panels; never replace or save StrategyIQ state. */
(() => {
  'use strict';
  const sidebar = document.getElementById('hubSidebar');
  const frame = document.getElementById('hubFrame');
  const toggle = document.getElementById('sidebarToggle');
  const close = document.getElementById('sidebarClose');
  const backdrop = document.getElementById('sidebarBackdrop');
  if (!sidebar || !frame || !toggle || !close || !backdrop) return;
  const mobile = window.matchMedia('(max-width: 1099px)');
  const panels = [...document.querySelectorAll('[data-hub-panel]')];
  const links = [...document.querySelectorAll('[data-hub-link]')];
  const routes = new Set(panels.map(panel => panel.dataset.hubPanel));
  const scrollPositions = new Map();
  const titles = {hub:'PMC Intelligence Hub', mission:'PMC Mission Control', clients:'PMC Client Profiles', strategy:'PMC StrategyIQ', competitoriq:'PMC CompetitorIQ', radar:'PMC Radar', launchpad:'PMC Launchpad', budget:'Media Budget & KPI Planner', performance:'Marketing Performance Analyzer', audience:'Audience & Messaging Builder', creative:'Creative Deliverables Planner', audit:'Campaign Launch Auditor'};
  let current = null;
  let open = false;
  let scrollLock = null;

  function jump(y) {
    const root = document.documentElement;
    const previous = root.style.scrollBehavior;
    root.style.scrollBehavior = 'auto';
    window.scrollTo(0, y);
    root.style.scrollBehavior = previous;
  }
  function lockScroll() {
    if (scrollLock) return;
    const body = document.body;
    scrollLock = {y:window.scrollY, position:body.style.position, top:body.style.top, width:body.style.width, overflow:body.style.overflow};
    body.style.position = 'fixed';
    body.style.top = '-' + scrollLock.y + 'px';
    body.style.width = '100%';
    body.style.overflow = 'hidden';
  }
  function unlockScroll() {
    if (!scrollLock) return;
    const saved = scrollLock;
    scrollLock = null;
    for (const key of ['position','top','width','overflow']) document.body.style[key] = saved[key];
    jump(saved.y);
  }
  function setDrawer(next, restoreFocus = true) {
    open = Boolean(next && mobile.matches);
    sidebar.classList.toggle('is-open', open);
    sidebar.inert = mobile.matches && !open;
    frame.inert = open;
    backdrop.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close navigation menu' : 'Open navigation menu');
    if (open) {
      sidebar.setAttribute('role', 'dialog');
      sidebar.setAttribute('aria-modal', 'true');
      lockScroll();
      sidebar.scrollTop = 0;
      close.focus({preventScroll:true});
    } else {
      sidebar.removeAttribute('role');
      sidebar.removeAttribute('aria-modal');
      unlockScroll();
      if (restoreFocus && mobile.matches) toggle.focus({preventScroll:true});
    }
  }
  function routeFromLocation() {
    const key = window.location.hash.slice(1).toLowerCase();
    if (routes.has(key)) return key;
    return document.body.dataset.authenticated === 'true' ? 'hub' : 'strategy';
  }
  function show(key, focus = true) {
    if (!routes.has(key)) return;
    setDrawer(false, false);
    if (current) scrollPositions.set(current, window.scrollY);
    for (const panel of panels) panel.hidden = panel.dataset.hubPanel !== key;
    for (const link of links) {
      if (link.dataset.hubLink === key) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    }
    current = key;
    document.body.dataset.hubView = key;
    document.title = key === 'hub' ? titles[key] : titles[key] + ' | PMC Intelligence Hub';
    const panel = panels.find(item => item.dataset.hubPanel === key);
    if (focus) panel?.querySelector('h1')?.focus({preventScroll:true});
    jump(scrollPositions.get(key) || 0);
  }
  for (const link of links) link.addEventListener('click', event => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const key = link.dataset.hubLink;
    if (!routes.has(key)) return;
    event.preventDefault();
    if (window.location.hash !== '#' + key) history.pushState(null, '', '#' + key);
    show(key);
  });
  toggle.addEventListener('click', () => setDrawer(!open));
  close.addEventListener('click', () => setDrawer(false));
  backdrop.addEventListener('click', () => setDrawer(false));
  sidebar.addEventListener('keydown', event => {
    if (!open) return;
    if (event.key === 'Escape') {event.preventDefault();setDrawer(false);return;}
    if (event.key !== 'Tab') return;
    const focusable = [...sidebar.querySelectorAll('a[href],button:not([disabled]),[tabindex="0"]')].filter(el => el.getClientRects().length && !el.hidden);
    const first = focusable[0], last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {event.preventDefault();last?.focus();}
    else if (!event.shiftKey && document.activeElement === last) {event.preventDefault();first?.focus();}
  });
  mobile.addEventListener('change', () => {
    const focusWasInside = sidebar.contains(document.activeElement);
    setDrawer(false, false);
    if (mobile.matches && focusWasInside) toggle.focus({preventScroll:true});
  });
  window.addEventListener('popstate', () => show(routeFromLocation()));
  window.addEventListener('hashchange', () => {const key=routeFromLocation();if(key !== current)show(key);});
  setDrawer(false, false);
  show(routeFromLocation(), false);
})();

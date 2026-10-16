/* ============================================================
   STRIKELINE — core.js
   Shared behavior on every page: Lenis smooth scroll, mobile
   menu, anchors, nav state, custom cursor, magnetic buttons,
   reveals, clip wipes, counters, curtain page transitions.
   Page-specific motion lives in its own file (home.js, ...).
   Requires: GSAP 3.12 + ScrollTrigger + Lenis (CDN, loaded first).
   ============================================================ */
const MOTION_READY = typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined';
const motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)');
let REDUCED = motionPreference.matches;
const FINE = window.matchMedia('(pointer: fine)').matches;
if (REDUCED) document.documentElement.classList.add('reduced');
let lenis = null;

/* Pins are reverted by ScrollTrigger's first matchMediaInit listener. Keep a
   viewport sample before that teardown; a raw scrollY cannot survive changing
   upstream pin space. Home owns visibility for focused horizontal program cards. */
let settledMotionPreference = motionPreference.matches;
let viewportAnchor = null;
let pendingMotionAnchor = null;
let anchorSampleFrame = 0;
let anchorRestoreFrame = 0;
let anchorStyle = null;
const anchorRoot = document.documentElement;
function sampleMotionAnchor() {
  anchorSampleFrame = 0;
  if (pendingMotionAnchor || motionPreference.matches !== settledMotionPreference) return;
  const focused = document.activeElement;
  const focusRect = focused?.getBoundingClientRect();
  const focusVisible = focused !== document.body && focusRect?.bottom > 0 &&
    focusRect.top < innerHeight && focusRect.right > 0 && focusRect.left < innerWidth;
  const hit = document.elementFromPoint(innerWidth / 2, innerHeight / 2);
  const element = focusVisible ? focused : hit?.closest(
    'h1,h2,h3,p,li,a,button,label,[data-facility-panel],.prog-card,section,footer'
  );
  if (!element || element.closest('#nav,.mobile-menu,#preloader,#curtain')) return;
  viewportAnchor = { element, top: element.getBoundingClientRect().top,
    focused: focused !== document.body ? focused : null };
}
function queueAnchorSample() {
  if (!anchorSampleFrame) anchorSampleFrame = requestAnimationFrame(sampleMotionAnchor);
}
function finishAnchorRestore() {
  cancelAnimationFrame(anchorRestoreFrame);
  anchorRestoreFrame = 0;
  pendingMotionAnchor = null;
  if (anchorStyle !== null) anchorRoot.style.overflowAnchor = anchorStyle;
  anchorStyle = null;
  settledMotionPreference = motionPreference.matches;
  queueAnchorSample();
}
function beginAnchorRestore() {
  if (motionPreference.matches === settledMotionPreference || pendingMotionAnchor) return;
  cancelAnimationFrame(anchorSampleFrame);
  anchorSampleFrame = 0;
  // Focus can already be BODY after a pin is removed, so use the saved element.
  if (!viewportAnchor || (viewportAnchor.element === viewportAnchor.focused &&
      viewportAnchor.focused?.closest('#hTrack'))) return;
  pendingMotionAnchor = { ...viewportAnchor };
  anchorStyle = anchorRoot.style.overflowAnchor;
  anchorRoot.style.overflowAnchor = 'none';
}
function restoreMotionAnchor() {
  if (!pendingMotionAnchor) {
    settledMotionPreference = motionPreference.matches;
    queueAnchorSample();
    return;
  }
  // All media contexts have rebuilt by GSAP's matchMedia event. Force its public
  // refresh here so an in-progress scroll cannot defer the new pin measurements.
  if (MOTION_READY) ScrollTrigger.refresh();
  let previousHeight = -1;
  let stableFrames = 0;
  let frames = 0;
  const restore = () => {
    const anchor = pendingMotionAnchor;
    if (!anchor?.element.isConnected) { finishAnchorRestore(); return; }
    if (anchor.focused?.isConnected && document.activeElement === document.body) {
      anchor.focused.focus({ preventScroll: true });
    }
    const delta = anchor.element.getBoundingClientRect().top - anchor.top;
    const height = anchorRoot.scrollHeight;
    if (Math.abs(delta) > .5) {
      const target = window.scrollY + delta;
      if (lenis) {
        lenis.resize();
        lenis.scrollTo(target, { immediate: true, force: true });
      } else window.scrollTo({ top: target, behavior: 'instant' });
      if (MOTION_READY) {
        ScrollTrigger.update();
        // A revealed ancestor must not replay its translation around typed input.
        for (let parent = anchor.element; parent; parent = parent.parentElement) {
          if (parent.hasAttribute('data-reveal')) {
            gsap.getTweensOf(parent).forEach(tween => tween.progress(1));
          }
        }
      }
    }
    stableFrames = Math.abs(delta) <= .5 && height === previousHeight ? stableFrames + 1 : 0;
    previousHeight = height;
    if (stableFrames >= 2 || ++frames >= 20) { finishAnchorRestore(); return; }
    anchorRestoreFrame = requestAnimationFrame(restore);
  };
  cancelAnimationFrame(anchorRestoreFrame);
  anchorRestoreFrame = requestAnimationFrame(restore);
}
window.addEventListener('scroll', queueAnchorSample, { passive: true });
window.addEventListener('resize', queueAnchorSample, { passive: true });
window.addEventListener('load', queueAnchorSample);
document.addEventListener('focusin', sampleMotionAnchor);
// A visitor's new scroll or keyboard action takes precedence over restoration.
['wheel', 'touchstart', 'keydown'].forEach(type => window.addEventListener(type, () => {
  if (pendingMotionAnchor) finishAnchorRestore();
}, { passive: true }));
if (MOTION_READY) {
  // A reveal may finish without another scroll event. Keep the saved element's
  // position current after GSAP renders, without repeating viewport hit testing.
  gsap.ticker.add(() => {
    if (viewportAnchor?.element.isConnected && !pendingMotionAnchor &&
        motionPreference.matches === settledMotionPreference) {
      viewportAnchor.top = viewportAnchor.element.getBoundingClientRect().top;
    }
  });
  gsap.addEventListener('matchMediaInit', beginAnchorRestore);
  gsap.addEventListener('matchMedia', restoreMotionAnchor);
}
motionPreference.addEventListener('change', event => {
  if (!MOTION_READY) beginAnchorRestore();
  REDUCED = event.matches;
  document.documentElement.classList.toggle('reduced', REDUCED || !MOTION_READY);
  if (!MOTION_READY) restoreMotionAnchor();
});
queueAnchorSample();

/* Shared keyboard/focus state, including the no-animation fallback. */
const menuButton = document.querySelector('.nav-burger');
const menuPanel = document.querySelector('.mobile-menu');
const backgroundInert = new Map();
function menuAccessibility(open, returnFocus = false) {
  if (!menuPanel || !menuButton) return;
  menuPanel.inert = !open;
  menuPanel.setAttribute('aria-hidden', String(!open));
  document.documentElement.classList.toggle('mobile-nav-open', open);
  if (open) {
    for (const el of document.body.children) {
      if (el === menuPanel || el.id === 'nav' || backgroundInert.has(el)) continue;
      backgroundInert.set(el, el.inert);
      el.inert = true;
    }
    menuPanel.scrollTop = 0;
    menuPanel.querySelector('a')?.focus({ preventScroll: true });
  } else {
    backgroundInert.forEach((value, el) => { el.inert = value; });
    backgroundInert.clear();
    if (returnFocus) menuButton.focus({ preventScroll: true });
  }
}
menuAccessibility(false);
document.addEventListener('keydown', event => {
  if (event.key !== 'Tab' || menuButton?.getAttribute('aria-expanded') !== 'true') return;
  const controls = [...document.querySelectorAll('#nav a, #nav button, .mobile-menu a')]
    .filter(el => el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden');
  const first = controls[0];
  const last = controls[controls.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault(); last?.focus({ preventScroll: true });
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault(); first?.focus({ preventScroll: true });
  }
});

if (!MOTION_READY) {
  // Keep content, forms and navigation usable when the animation CDN is unavailable.
  document.documentElement.classList.add('motion-unavailable', 'reduced');
  const fallbackBurger = document.querySelector('.nav-burger');
  const fallbackMenu = document.querySelector('.mobile-menu');
  function setFallbackMenu(open, returnFocus = false) {
    if (!fallbackMenu || !fallbackBurger) return;
    fallbackBurger.setAttribute('aria-expanded', String(open));
    fallbackMenu.style.visibility = open ? 'visible' : 'hidden';
    fallbackMenu.style.transform = open ? 'translateY(0)' : 'translateY(-100%)';
    menuAccessibility(open, returnFocus);
  }
  setFallbackMenu(false);
  if (fallbackBurger) fallbackBurger.addEventListener('click', () => {
    const open = fallbackBurger.getAttribute('aria-expanded') !== 'true';
    setFallbackMenu(open, !open);
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && fallbackBurger?.getAttribute('aria-expanded') === 'true') {
      setFallbackMenu(false, true);
    }
  });
  document.querySelectorAll('.mobile-menu a').forEach(link => {
    link.addEventListener('click', () => setFallbackMenu(false));
  });
  document.querySelectorAll('a[href="#"]').forEach(link => {
    link.addEventListener('click', event => event.preventDefault());
  });
  window.matchMedia('(min-width: 1201px)').addEventListener('change', event => {
    if (event.matches) setFallbackMenu(false);
  });
} else {
gsap.registerPlugin(ScrollTrigger);

function scrollToTarget(t) {
  if (lenis) {
    // A reveal's temporary translation must not push the settled target under the nav.
    const margin = Math.max(72, parseFloat(getComputedStyle(t).scrollMarginTop) || 0);
    const revealY = t.hasAttribute('data-reveal') ? Number(gsap.getProperty(t, 'y')) || 0 : 0;
    lenis.scrollTo(t, { offset: -margin - revealY, duration: 1.4 });
  }
  else t.scrollIntoView({ behavior: REDUCED ? 'auto' : 'smooth' });
}

/* ---------- mobile menu ---------- */
const burger = document.querySelector('.nav-burger');
const mMenu = document.querySelector('.mobile-menu');
let menuOpen = false;
let menuTween = null;
if (mMenu) gsap.set(mMenu, { yPercent: -100, visibility: 'hidden' });

function closeMenu(returnFocus = false) {
  if (!menuOpen || !mMenu) return;
  menuOpen = false;
  burger.setAttribute('aria-expanded', 'false');
  menuTween?.kill();
  menuAccessibility(false, returnFocus);
  if (REDUCED) {
    gsap.set(mMenu, { yPercent: -100, visibility: 'hidden' });
  } else {
    menuTween = gsap.timeline({ onComplete: () => gsap.set(mMenu, { visibility: 'hidden' }) })
      .to('.mobile-menu .mm-link, .mobile-menu .mm-cta', { opacity: 0, y: -24, duration: .25, ease: 'power2.in', stagger: .03 })
      .to(mMenu, { yPercent: -100, duration: .45, ease: 'power3.inOut' }, '-=.1')
      .set('.mobile-menu .mm-link, .mobile-menu .mm-cta', { clearProps: 'opacity,y' });
  }
  if (lenis) lenis.start();
}
function openMenu() {
  if (!mMenu) return;
  menuOpen = true;
  menuTween?.kill();
  burger.setAttribute('aria-expanded', 'true');
  gsap.set('.mobile-menu .mm-link, .mobile-menu .mm-cta', { clearProps: 'opacity,y' });
  gsap.set(mMenu, { visibility: 'visible' });
  if (REDUCED) {
    gsap.set(mMenu, { yPercent: 0 });
  } else {
    menuTween = gsap.timeline()
      .to(mMenu, { yPercent: 0, duration: .55, ease: 'power3.inOut' })
      .from('.mobile-menu .mm-link', { y: 56, opacity: 0, duration: .55, ease: 'power3.out', stagger: .07 }, '-=.2')
      .from('.mobile-menu .mm-cta', { opacity: 0, y: 18, duration: .45, ease: 'power3.out' }, '-=.35');
  }
  if (lenis) lenis.stop();
  menuAccessibility(true);
}
if (burger) burger.addEventListener('click', () => (menuOpen ? closeMenu(true) : openMenu()));
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && menuOpen) closeMenu(true);
});
window.matchMedia('(min-width: 1201px)').addEventListener('change', event => {
  if (event.matches) closeMenu();
});
motionPreference.addEventListener('change', () => {
  menuTween?.kill();
  if (mMenu) gsap.set(mMenu, {
    yPercent: menuOpen ? 0 : -100, visibility: menuOpen ? 'visible' : 'hidden'
  });
  gsap.set('.mobile-menu .mm-link, .mobile-menu .mm-cta', { clearProps: 'opacity,y' });
});

/* ---------- anchors + inert placeholder links ---------- */
document.querySelectorAll('a[href]').forEach(a => {
  const raw = a.getAttribute('href');
  if (raw === '#') { a.addEventListener('click', e => e.preventDefault()); return; }
  if (raw[0] !== '#' && !raw.includes('.html#')) return;
  a.addEventListener('click', e => {
    const url = new URL(a.href);
    const path = value => value.replace(/index\.html$/, '').replace(/\.html$/, '');
    if (url.origin !== location.origin || path(url.pathname) !== path(location.pathname) || !url.hash) return;
    const t = document.querySelector(url.hash);
    if (!t) return;
    e.preventDefault();
    closeMenu();
    scrollToTarget(t);
    history.replaceState(null, '', url.hash);
  });
});

/* landing with a hash (e.g. index.html#apply from another page) */
if (location.hash) {
  const t = document.querySelector(location.hash);
  if (t) window.addEventListener('load', () => setTimeout(() => scrollToTarget(t), 60));
}

/* ---------- nav state ---------- */
const nav = document.getElementById('nav');
if (nav) ScrollTrigger.create({ start: 80, toggleClass: { targets: nav, className: 'scrolled' } });

/* current page marker */
const page = (location.pathname.split('/').pop() || 'index').replace(/\.html$/, '');
document.querySelectorAll('.nav-links a, .mm-link').forEach(a => {
  if (a.getAttribute('href').replace(/\.html$/, '') === page) a.setAttribute('aria-current', 'page');
});

/* Pointer listeners belong to the active motion context and are removed on reduction. */
function pointerMotion() {
  if (!FINE) return () => {};
  const listeners = [];
  const listen = (element, event, handler) => {
    element.addEventListener(event, handler);
    listeners.push(() => element.removeEventListener(event, handler));
  };
  const dot = document.getElementById('cursorDot');
  const ring = document.getElementById('cursorRing');
  if (dot && ring) {
    const dx = gsap.quickTo(dot, 'x', { duration: .12, ease: 'power2.out' });
    const dy = gsap.quickTo(dot, 'y', { duration: .12, ease: 'power2.out' });
    const rx = gsap.quickTo(ring, 'x', { duration: .45, ease: 'power3.out' });
    const ry = gsap.quickTo(ring, 'y', { duration: .45, ease: 'power3.out' });
    listen(window, 'mousemove', e => { dx(e.clientX); dy(e.clientY); rx(e.clientX); ry(e.clientY); });
    document.querySelectorAll('a,button,input,select,textarea,.method-row,.pos-cell,.prog-card,.coach-card,.exp-head').forEach(el => {
      listen(el, 'mouseenter', () => ring.classList.add('grow'));
      listen(el, 'mouseleave', () => ring.classList.remove('grow'));
    });
  }
  const magnets = [...document.querySelectorAll('.magnetic')];
  magnets.forEach(el => {
    listen(el, 'mousemove', e => {
      const r = el.getBoundingClientRect();
      gsap.to(el, { x: (e.clientX - r.left - r.width / 2) * .28,
        y: (e.clientY - r.top - r.height / 2) * .28, duration: .4,
        ease: 'power2.out', overwrite: 'auto' });
    });
    listen(el, 'mouseleave', () => gsap.to(el, {
      x: 0, y: 0, duration: .7, ease: 'elastic.out(1,.4)', overwrite: 'auto'
    }));
  });
  return () => {
    listeners.forEach(remove => remove());
    ring?.classList.remove('grow');
    gsap.killTweensOf(magnets);
    if (magnets.length) gsap.set(magnets, { clearProps: 'transform' });
  };
}

/* ---------- split headlines (scroll-triggered char reveals) ---------- */
function splitHeadline(el) {
  const frag = document.createDocumentFragment();
  const wrapText = (text, cls) => {
    text.split(/(\s+)/).forEach(part => {
      if (!part) return;
      if (/^\s+$/.test(part)) { frag.appendChild(document.createTextNode(' ')); return; }
      const w = document.createElement('span');
      w.className = 'sw';
      [...part].forEach(c => {
        const s = document.createElement('span');
        s.className = 'sch' + (cls ? ' ' + cls : '');
        s.textContent = c;
        w.appendChild(s);
      });
      frag.appendChild(w);
    });
  };
  [...el.childNodes].forEach(n => {
    if (n.nodeName === 'BR') { frag.appendChild(document.createElement('br')); return; }
    const cls = n.nodeType === 1 ? ((n.className || '') + (n.nodeName === 'EM' ? ' em' : '')).trim() : '';
    wrapText(n.textContent, cls);
  });
  el.innerHTML = '';
  el.appendChild(frag);
}
document.querySelectorAll('[data-split-scroll]').forEach(splitHeadline);
const counterStates = [...document.querySelectorAll('[data-count]')].map(el => ({
  el, end: Number(el.dataset.count), sup: el.querySelector('sup')?.outerHTML || ''
}));
const curtain = document.getElementById('curtain');
let curtainTween = null;

/* Scoped motion is reverted before the static branch or a fresh normal branch runs. */
const coreMotion = gsap.matchMedia();
coreMotion.add({ normal: '(prefers-reduced-motion: no-preference)',
  reduced: '(prefers-reduced-motion: reduce)' }, context => {
  if (context.conditions.reduced) {
    gsap.set('.sch', { y: 0 });
    gsap.set('[data-reveal]', { opacity: 1, y: 0 });
    gsap.set('[data-clip]', { clipPath: 'none' });
    if (curtain) gsap.set(curtain, { yPercent: 100 });
    counterStates.forEach(({ el, end, sup }) => { el.innerHTML = end + sup; });
    return;
  }

  let smooth = null;
  let smoothTick = null;
  if (typeof Lenis !== 'undefined') {
    smooth = new Lenis({ lerp: 0.09 });
    lenis = smooth;
    smooth.on('scroll', ScrollTrigger.update);
    smoothTick = time => smooth.raf(time * 1000);
    gsap.ticker.add(smoothTick);
    gsap.ticker.lagSmoothing(0);
    if (menuOpen) smooth.stop();
  }
  const stopPointer = pointerMotion();
  const counterTweens = [];
  document.querySelectorAll('[data-split-scroll]').forEach(el => {
    gsap.to(el.querySelectorAll('.sch'), { y: 0, duration: .9,
      ease: 'power4.out', stagger: .018,
      scrollTrigger: { trigger: el, start: 'top 86%' } });
  });

  /* Reveals, clip wipes and footer wordmark. */
  const grouped = new Set();
  gsap.utils.toArray('[data-reveal-group]').forEach(g => {
    const kids = [...g.querySelectorAll('[data-reveal]')];
    kids.forEach(k => grouped.add(k));
    gsap.to(kids, { opacity: 1, y: 0, duration: 1, ease: 'power3.out', stagger: .09,
      scrollTrigger: { trigger: g, start: 'top 86%' } });
  });
  gsap.utils.toArray('[data-reveal]').forEach(el => {
    if (grouped.has(el)) return;
    gsap.to(el, { opacity: 1, y: 0, duration: 1, ease: 'power3.out',
      scrollTrigger: { trigger: el, start: 'top 88%' } });
  });
  gsap.utils.toArray('[data-clip]').forEach(el => {
    gsap.to(el, { clipPath: 'inset(0 0 0% 0)', duration: 1.2, ease: 'power3.inOut',
      scrollTrigger: { trigger: el, start: 'top 85%' } });
  });
  if (document.querySelector('.foot-word')) {
    gsap.from('.foot-word', { yPercent: 34, opacity: 0, duration: 1.2, ease: 'power3.out',
      scrollTrigger: { trigger: '.foot-word', start: 'top 96%' } });
  }
  counterStates.forEach(({ el, end, sup }) => {
    ScrollTrigger.create({ trigger: el, start: 'top 88%', once: true, onEnter: () => {
      counterTweens.push(gsap.to({ v: 0 }, { v: end, duration: 1.6, ease: 'power2.out',
        onUpdate: function () { el.innerHTML = Math.round(this.targets()[0].v) + sup; } }));
    } });
  });
  return () => {
    if (smoothTick) gsap.ticker.remove(smoothTick);
    smooth?.destroy();
    if (lenis === smooth) lenis = null;
    stopPointer();
    counterTweens.forEach(tween => tween.kill());
    // A preference change must not cancel a navigation that the visitor chose.
    curtainTween?.progress(1);
    curtainTween?.kill();
    curtainTween = null;
  };
});

/* ---------- curtain page transitions (internal .html links) ---------- */
if (curtain) {
  if (sessionStorage.getItem('sl-curtain') === '1') {
    sessionStorage.removeItem('sl-curtain');
    if (!REDUCED) curtainTween = gsap.fromTo(curtain, {
      yPercent: 0
    }, { yPercent: -100, duration: .5, ease: 'power3.inOut', delay: .05,
      onComplete: () => gsap.set(curtain, { yPercent: 100 }) });
  }
  document.querySelectorAll('a[href]').forEach(a => {
    const raw = a.getAttribute('href');
    if (!/\.html(#|$)/.test(raw) || a.target === '_blank' || a.hasAttribute('download')) return;
    a.addEventListener('click', e => {
      if (REDUCED) return;
      const url = new URL(a.href);
      const path = value => value.replace(/index\.html$/, '').replace(/\.html$/, '');
      if (url.origin !== location.origin || path(url.pathname) === path(location.pathname)) return;
      e.preventDefault();
      closeMenu();
      curtainTween = gsap.timeline({ onComplete: () => {
        sessionStorage.setItem('sl-curtain', '1');
        location.href = url.href;
      } })
      .set(curtain, { yPercent: 100 })
      .to(curtain, { yPercent: 0, duration: .45, ease: 'power3.inOut' });
    });
  });
  window.addEventListener('pageshow', e => { if (e.persisted) gsap.set(curtain, { yPercent: 100 }); });
}
}

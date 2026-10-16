/* ============================================================
   STRIKELINE — expanders.js
   Subpage interactions: services lane tabs/background media,
   product menu expanders and coach bio expanders.
   One open per group, with isolated focus and live motion preferences.
   Requires core.js first; animations also use the optional GSAP CDN.
   ============================================================ */

const expanderMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
let nextExpanderId = 0;
function ensureExpanderId(element, prefix) {
  if (element.id) return element.id;
  let id;
  do { id = prefix + '-' + ++nextExpanderId; } while (document.getElementById(id));
  element.id = id;
  return id;
}

/* ---------- generic expander groups (products, coaches) ---------- */
document.querySelectorAll('[data-exp-group]').forEach(group => {
  const items = [...group.querySelectorAll('.exp-item')].map(item => ({
    item, head: item.querySelector('.exp-head'), panel: item.querySelector('.exp-panel'),
  })).filter(state => state.head && state.panel);
  function setOpen(state, open) {
    if (!open && state.panel.contains(document.activeElement)) {
      state.head.focus({ preventScroll: true });
    }
    state.item.classList.toggle('open', open);
    state.head.setAttribute('aria-expanded', String(open));
    state.panel.inert = !open;
    state.panel.setAttribute('aria-hidden', String(!open));
  }
  const initiallyOpen = items.find(state => state.item.classList.contains('open'));
  items.forEach(state => {
    const { item, head, panel } = state;
    const panelId = ensureExpanderId(panel, (item.id || 'expander') + '-panel');
    const headId = ensureExpanderId(head, panelId + '-toggle');
    head.setAttribute('aria-controls', panelId);
    panel.setAttribute('aria-labelledby', headId);
    panel.setAttribute('role', 'region');
    if (head.tagName === 'BUTTON') head.type = 'button';
    setOpen(state, state === initiallyOpen);
    const toggle = () => {
      const isOpen = item.classList.contains('open');
      items.forEach(other => setOpen(other, other === state && !isOpen));
    };
    head.addEventListener('click', e => {
      if (e.target.closest('a')) return;
      toggle();
    });
    head.addEventListener('keydown', e => {
      // Native buttons already activate once for Enter/Space. Retain non-button hook support.
      if (head.tagName === 'BUTTON' || e.target.closest('a')
        || (e.key !== 'Enter' && e.key !== ' ')) return;
      e.preventDefault();
      toggle();
    });
  });
  group.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    const open = items.find(state => state.item.classList.contains('open'));
    if (!open) return;
    e.preventDefault();
    e.stopPropagation();
    setOpen(open, false);
    open.head.focus({ preventScroll: true });
  });
});

/* ---------- services lane tabs (+ background slideshow sync) ---------- */
const laneBgs = [...document.querySelectorAll('[data-lane-bg]')];
let laneBackgroundInView = false;
function syncLaneVideos() {
  laneBgs.forEach(bg => bg.querySelectorAll('video').forEach(video => {
    const play = bg.classList.contains('active') && video.classList.contains('on')
      && laneBackgroundInView && !document.hidden && !expanderMotionQuery.matches;
    if (play) video.play().catch(() => {});
    else video.pause();
  }));
}
document.querySelectorAll('[data-tabs]').forEach(root => {
  const tabs = [...root.querySelectorAll('.lane-tab')];
  const panels = [...root.querySelectorAll('.lane-panel')];
  if (!tabs.length) return;
  const tablist = root.querySelector('[role="tablist"]');
  const vertical = window.matchMedia('(max-width: 700px)');
  const orientation = () => {
    if (tablist) {
      tablist.setAttribute('aria-orientation', vertical.matches ? 'vertical' : 'horizontal');
    }
  };
  orientation();
  vertical.addEventListener('change', orientation);
  tabs.forEach((tab, i) => {
    if (!panels[i]) return;
    const tabId = ensureExpanderId(tab, 'lane-tab');
    const panelId = ensureExpanderId(panels[i], 'lane-panel');
    tab.setAttribute('aria-controls', panelId);
    panels[i].setAttribute('aria-labelledby', tabId);
    panels[i].tabIndex = 0;
    tab.addEventListener('click', () => activate(i));
    tab.addEventListener('keydown', e => {
      let next = i;
      if (e.key === 'Home') next = 0;
      else if (e.key === 'End') next = tabs.length - 1;
      else if (e.key === (vertical.matches ? 'ArrowDown' : 'ArrowRight')) {
        next = (i + 1) % tabs.length;
      } else if (e.key === (vertical.matches ? 'ArrowUp' : 'ArrowLeft')) {
        next = (i + tabs.length - 1) % tabs.length;
      } else return;
      e.preventDefault();
      activate(next);
      tabs[next].focus();
    });
  });
  function activate(index, animate = true) {
    tabs.forEach((tab, i) => {
      const on = i === index;
      tab.classList.toggle('active', on);
      tab.setAttribute('aria-selected', String(on));
      tab.tabIndex = on ? 0 : -1;
      if (panels[i]) {
        panels[i].classList.toggle('active', on);
        panels[i].hidden = !on;
        panels[i].inert = !on;
        panels[i].setAttribute('aria-hidden', String(!on));
      }
      if (laneBgs[i]) laneBgs[i].classList.toggle('active', on);
    });
    syncLaneVideos();
    if (MOTION_READY) {
      gsap.killTweensOf(panels);
      gsap.set(panels, { clearProps: 'opacity,transform' });
      if (animate && !expanderMotionQuery.matches && panels[index]) {
        gsap.fromTo(panels[index], { opacity: 0, y: 24 }, {
          opacity: 1, y: 0, duration: .6, ease: 'power3.out', clearProps: 'opacity,transform',
        });
      }
    }
  }
  activate(Math.max(0, tabs.findIndex(tab => tab.classList.contains('active'))), false);
  expanderMotionQuery.addEventListener('change', () => {
    if (expanderMotionQuery.matches && MOTION_READY) {
      gsap.killTweensOf(panels);
      gsap.set(panels, { clearProps: 'opacity,transform' });
    }
  });
});

/* ---------- lane background rotation: 7s still→video→still on the active lane ---------- */
if (laneBgs.length) {
  const media = laneBgs.map(b => [...b.children]);
  const idx = laneBgs.map(() => 0);
  let timer = null;
  const show = (bi, ni) => {
    media[bi].forEach((el, i) => {
      const on = i === ni;
      el.classList.toggle('on', on);
      if (el.tagName === 'VIDEO' && on) el.currentTime = 0;
    });
    syncLaneVideos();
  };
  const lanesSec = document.getElementById('lanes');
  if (lanesSec) new IntersectionObserver(entries => {
    laneBackgroundInView = entries[0].isIntersecting;
    syncLaneVideos();
  }, { threshold: .05 }).observe(lanesSec);
  function updateMotion() {
    window.clearInterval(timer);
    timer = null;
    if (expanderMotionQuery.matches) {
      laneBgs.forEach((bg, bi) => {
        idx[bi] = 0;
        show(bi, 0);
      });
    } else {
      timer = window.setInterval(() => {
        if (document.hidden) return;
        const ai = laneBgs.findIndex(bg => bg.classList.contains('active'));
        if (ai < 0 || !media[ai].length) return;
        idx[ai] = (idx[ai] + 1) % media[ai].length;
        show(ai, idx[ai]);
      }, 7000);
    }
    syncLaneVideos();
  }
  expanderMotionQuery.addEventListener('change', updateMotion);
  document.addEventListener('visibilitychange', syncLaneVideos);
  updateMotion();
}

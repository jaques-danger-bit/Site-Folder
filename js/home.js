/* ============================================================
   STRIKELINE — home.js
   Homepage preloader, hero entrance, parallax, doctrine, program
   media/pin and drawers. Load after facility.js and core.js so
   downstream triggers account for the approved gym tour pin.
   Decorative readiness is bounded; motion contexts clean up on
   preference changes. Forms remain owned by form-delivery.js.
   ============================================================ */

(() => {
  const SHIELD_SVG_URL = 'assets/media/logos/brand/logo-shield.svg';

  function createShieldScene(canvas) {
    if (!canvas || typeof THREE === 'undefined' || !THREE.SVGLoader) return null;
    const host = canvas.parentElement;
    let renderer;
    try {
      const settings = { alpha: true, antialias: true, powerPreference: 'high-performance' };
      const context = canvas.getContext('webgl2', settings) || canvas.getContext('webgl', settings);
      if (!context) return null;
      renderer = new THREE.WebGLRenderer({ canvas, context, ...settings });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
      renderer.outputEncoding = THREE.sRGBEncoding;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = .82;
    } catch (_) {
      renderer?.dispose();
      return null;
    }

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(27, 1, .1, 100);
    camera.position.set(0, 0, 4.8);
    const root = new THREE.Group();
    scene.add(root);
    scene.add(new THREE.HemisphereLight(0x7b7b80, 0x08080a, .72));
    const key = new THREE.DirectionalLight(0xffffff, 1.15);
    key.position.set(-3, 4, 5);
    scene.add(key);
    const rim = new THREE.PointLight(0xc23026, 1.8, 12);
    rim.position.set(3.4, .4, 2.6);
    scene.add(rim);

    let disposed = false;
    let frame = 0;
    let resizeObserver = null;
    let resolveReady;
    const state = { root, readyPromise: new Promise(resolve => { resolveReady = resolve; }) };
    const resize = () => {
      if (disposed) return;
      const rect = host.getBoundingClientRect();
      const width = Math.max(1, Math.round(rect.width));
      const height = Math.max(1, Math.round(rect.height));
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };
    const lost = event => { event.preventDefault(); state.dispose(); };
    state.dispose = () => {
      if (disposed) return;
      disposed = true;
      cancelAnimationFrame(frame);
      resizeObserver?.disconnect();
      canvas.removeEventListener('webglcontextlost', lost);
      scene.traverse(child => {
        child.geometry?.dispose();
        const materials = Array.isArray(child.material) ? child.material : [child.material];
        materials.forEach(material => material?.dispose());
      });
      renderer.dispose();
      host.classList.remove('three-ready');
      resolveReady(false);
    };
    canvas.addEventListener('webglcontextlost', lost);
    try {
      resize();
      if (window.ResizeObserver) {
        resizeObserver = new ResizeObserver(resize);
        resizeObserver.observe(host);
      }
      new THREE.SVGLoader().load(SHIELD_SVG_URL, data => {
        if (disposed) return;
        try {
          const model = new THREE.Group();
          const faceMaterial = new THREE.MeshPhysicalMaterial({ color: 0x5f0b1b,
            roughness: .64, metalness: .03, clearcoat: .12, clearcoatRoughness: .78 });
          const edgeMaterial = new THREE.MeshPhysicalMaterial({
            color: 0x2f030b, roughness: .72, metalness: .02
          });
          data.paths.forEach(path => {
            THREE.SVGLoader.createShapes(path).forEach(shape => {
              const geometry = new THREE.ExtrudeGeometry(shape, { depth: 72,
                bevelEnabled: true, bevelThickness: 14, bevelSize: 9,
                bevelSegments: 3, curveSegments: 3 });
              geometry.computeVertexNormals();
              model.add(new THREE.Mesh(geometry, [faceMaterial, edgeMaterial]));
            });
          });
          const box = new THREE.Box3().setFromObject(model);
          const size = box.getSize(new THREE.Vector3());
          const center = box.getCenter(new THREE.Vector3());
          const scale = 1.82 / Math.max(size.x, size.y, size.z);
          model.position.set(-center.x, -center.y, -center.z);
          const normalized = new THREE.Group();
          normalized.scale.set(scale, -scale, scale);
          normalized.add(model);
          root.add(normalized);
          host.classList.add('three-ready');
          resolveReady(true);
        } catch (_) { state.dispose(); }
      }, undefined, () => state.dispose());
    } catch (_) {
      state.dispose();
      return null;
    }
    const render = () => {
      if (disposed) return;
      try { renderer.render(scene, camera); }
      catch (_) { state.dispose(); return; }
      frame = requestAnimationFrame(render);
    };
    frame = requestAnimationFrame(render);
    return state;
  }

  /* Drawers remain interactive even when animation libraries are unavailable. */
  const progCards = [...document.querySelectorAll('.prog-card')];
  function setCardOpen(card, open) {
    const drawer = card.querySelector('.prog-drawer');
    if (!open && drawer?.contains(document.activeElement)) card.focus({ preventScroll: true });
    card.classList.toggle('open', open);
    card.setAttribute('aria-expanded', String(open));
    if (drawer) {
      drawer.inert = !open;
      drawer.setAttribute('aria-hidden', String(!open));
    }
  }
  progCards.forEach((card, index) => {
    const drawer = card.querySelector('.prog-drawer');
    if (drawer) {
      drawer.id = drawer.id || 'program-details-' + (index + 1);
      card.setAttribute('aria-controls', drawer.id);
    }
    setCardOpen(card, false);
    const toggle = () => {
      const open = !card.classList.contains('open');
      progCards.forEach(other => setCardOpen(other, false));
      if (open) {
        setCardOpen(card, true);
        card.focus({ preventScroll: true });
      }
    };
    card.addEventListener('click', event => {
      if (!event.target.closest('a,button,input,select,textarea')) toggle();
    });
    card.addEventListener('keydown', event => {
      if (event.key === 'Escape' && card.classList.contains('open')) {
        event.preventDefault();
        setCardOpen(card, false);
        card.focus({ preventScroll: true });
        return;
      }
      if (event.target !== card || !['Enter', ' '].includes(event.key)) return;
      event.preventDefault();
      toggle();
    });
  });

  if (!MOTION_READY) return;

  /* Split once; preference changes never nest the generated markup. */
  document.querySelectorAll('[data-split]').forEach(line => {
    const fragment = document.createDocumentFragment();
    [...line.childNodes].forEach(node => {
      const cls = node.nodeType === 1
        ? ((node.className || '') + (node.nodeName === 'EM' ? ' em' : '')).trim() : '';
      [...node.textContent].forEach(character => {
        const span = document.createElement('span');
        span.className = 'ch' + (cls ? ' ' + cls : '');
        span.textContent = character === ' ' ? '\u00a0' : character;
        fragment.appendChild(span);
      });
    });
    line.replaceChildren(fragment);
  });
  const manifesto = document.getElementById('manifestoText');
  if (manifesto) {
    const accents = ['science', 'progress'];
    const fragment = document.createDocumentFragment();
    manifesto.textContent.trim().split(/\s+/).forEach((word, index) => {
      if (index) fragment.appendChild(document.createTextNode(' '));
      const span = document.createElement('span');
      const clean = word.replace(/[^a-z.]/gi, '').toLowerCase();
      span.className = 'w' + (accents.includes(clean) ? ' accent-w' : '');
      span.textContent = word;
      fragment.appendChild(span);
    });
    manifesto.replaceChildren(fragment);
  }

  const preloader = document.getElementById('preloader');
  const loaderShield = document.querySelector('.loader-shield');
  const skipLoader = new URLSearchParams(location.search).has('skipLoader') ||
    window.strikelineMotionLibrariesReady === false;
  const doctrineImages = [...document.querySelectorAll('.doc-bg img')];
  const buckets = [...document.querySelectorAll('[data-rotate]')];
  let heroEntered = false;
  let loaderFinished = false;
  const programTrack = document.getElementById('hTrack');
  let programFocused = null;
  let programFocusVisible = false;
  let programRestoringFocus = false;
  let programMotionReduced = motionPreference.matches;
  let programFocusBeforeMotion = null;
  let revealProgramFocus = null;
  // ScrollTrigger's earlier matchMediaInit listener reparents pins and can drop
  // focus before Home's listener runs. Keep the last stable focus independently
  // of those transient events, then restore after all pins have been refreshed.
  const rememberProgramVisibility = () => {
    if (motionPreference.matches !== programMotionReduced || programRestoringFocus) return;
    const bounds = programFocused?.getBoundingClientRect();
    const navBottom = document.querySelector('nav')?.getBoundingClientRect().bottom || 0;
    programFocusVisible = Boolean(bounds && bounds.right > 0 && bounds.left < innerWidth &&
      bounds.bottom > navBottom && bounds.top < innerHeight);
  };
  document.addEventListener('focusin', event => {
    if (motionPreference.matches !== programMotionReduced || programRestoringFocus) return;
    programFocused = programTrack?.contains(event.target) ? event.target : null;
    rememberProgramVisibility();
  });
  document.addEventListener('focusout', () => {
    Promise.resolve().then(() => {
      if (motionPreference.matches === programMotionReduced &&
          !programTrack?.contains(document.activeElement)) {
        programFocused = null;
        programFocusVisible = false;
      }
    });
  });
  window.addEventListener('scroll', rememberProgramVisibility, { passive: true });
  gsap.addEventListener('matchMediaInit', () => {
    programFocusBeforeMotion = { active: programFocused, visible: programFocusVisible };
  });
  gsap.addEventListener('matchMedia', () => {
    const saved = programFocusBeforeMotion;
    const active = saved?.active;
    programFocusBeforeMotion = null;
    programMotionReduced = motionPreference.matches;
    if (!active?.isConnected) return;
    programRestoringFocus = true;
    active.focus({ preventScroll: true });
    programRestoringFocus = false;
    // A visitor can scroll away while a program control keeps focus. Preserve
    // that identity without taking the viewport away from their reading place.
    if (saved.visible) revealProgramFocus?.(active);
    rememberProgramVisibility();
  });
  const staticMedia = () => {
    doctrineImages.forEach((image, index) => image.classList.toggle('on', index === 0));
    buckets.forEach(bucket => [...bucket.children].forEach((element, index) => {
      element.classList.toggle('on', index === 0);
      if (element.tagName === 'VIDEO') element.pause();
    }));
  };

  const homeMotion = gsap.matchMedia();
  homeMotion.add({ normal: '(prefers-reduced-motion: no-preference)',
    reduced: '(prefers-reduced-motion: reduce)' }, context => {
    if (context.conditions.reduced) {
      if (preloader) gsap.set(preloader, { display: 'none' });
      gsap.set('.hero h1 .ch', { y: 0, rotate: 0 });
      gsap.set('.hero-eyebrow, .hero-sub, nav', { opacity: 1, y: 0 });
      gsap.set('#manifestoText .w', { opacity: 1, transition: 'none' });
      gsap.set('#hBar', { scaleX: 1 });
      heroEntered = true;
      loaderFinished = true;
      staticMedia();
      revealProgramFocus = active => {
        active.closest('.prog-card')?.scrollIntoView({ block: 'nearest', inline: 'center' });
        active.scrollIntoView({ block: 'nearest', inline: 'nearest' });
      };
      return () => { revealProgramFocus = null; };
    }

    let disposed = false;
    let loader3D = null;
    let readinessTimer = 0;
    const cleanups = [];
    const heroIn = !heroEntered ? gsap.timeline({ paused: true,
      onComplete: () => { heroEntered = true; } })
      .from('.hero-eyebrow', { opacity: 0, y: 16, duration: .55, ease: 'power3.out' })
      .to('.hero h1 .ch', { y: 0, rotate: 0, duration: 1,
        ease: 'power4.out', stagger: .022 }, '-=.3')
      .from('.hero-sub', { opacity: 0, y: 30, duration: .9, ease: 'power3.out' }, '-=.7')
      .from('nav', { opacity: 0, y: -20, duration: .8, ease: 'power3.out' }, '-=.8') : null;
    if (!heroIn) {
      gsap.set('.hero h1 .ch', { y: 0, rotate: 0 });
      gsap.set('.hero-eyebrow, .hero-sub, nav', { opacity: 1, y: 0 });
    }
    if (skipLoader || loaderFinished || !preloader) {
      if (preloader) gsap.set(preloader, { display: 'none' });
      heroIn?.play();
      loaderFinished = true;
    } else {
      const loaderTimeline = gsap.timeline({ paused: true })
        .set(loaderShield, { opacity: 0, scale: .72, rotationX: 0 })
        .set('.loader-fallback', { rotationY: -155, transformPerspective: 1100 })
        .to(loaderShield, { opacity: 1, scale: 1, duration: .42,
          ease: 'power4.out', delay: .06 })
        .to('.loader-fallback', { rotationY: 0, duration: .42, ease: 'power4.out' }, '<')
        .to('.loader-fallback', { rotationY: 360, duration: .67, ease: 'power2.inOut' }, '+=.03')
        .to('.loader-fallback', { rotationY: 366, duration: .08, ease: 'power1.out' })
        .to('.loader-fallback', { rotationY: 360, duration: .12, ease: 'power2.out' })
        .to(loaderShield, { scale: .88, y: -8, opacity: .72, duration: .22,
          ease: 'power2.in' }, '+=.05')
        .add(() => heroIn?.play(), '-=.08')
        .to(preloader, { opacity: 0, duration: .48, ease: 'power2.inOut' }, '-=.08')
        .set(preloader, { display: 'none' })
        .add(() => { loaderFinished = true; loader3D?.dispose(); });

      // One deadline covers the optional library AND model request. Late callbacks
      // cannot revive a scene or timeline after reduction or the deadline.
      new Promise(resolve => {
        let settled = false;
        const finish = ready => {
          if (settled) return;
          settled = true;
          clearTimeout(readinessTimer);
          if (!ready) { loader3D?.dispose(); loader3D = null; }
          resolve(ready);
        };
        readinessTimer = setTimeout(() => finish(false), 1800);
        const libraryReady = window.strikelineShieldLoaderReady ||
          Promise.resolve(typeof THREE !== 'undefined' && Boolean(THREE.SVGLoader));
        Promise.resolve(libraryReady).then(ready => {
          if (disposed || settled || !ready) { finish(false); return; }
          loader3D = createShieldScene(document.getElementById('shieldCanvas'));
          if (!loader3D) { finish(false); return; }
          loader3D.readyPromise.then(finish, () => finish(false));
        }, () => finish(false));
      }).then(ready => {
        if (disposed) return;
        if (ready && loader3D) {
          loaderTimeline
            .set(loader3D.root.rotation, { y: -Math.PI * .62 }, 0)
            .to(loader3D.root.rotation, { y: 0, duration: .48, ease: 'power4.out' }, .06)
            .to(loader3D.root.rotation, { y: Math.PI * 2, duration: .9,
              ease: 'power3.inOut' }, .5)
            .to(loader3D.root.rotation, { y: Math.PI * 2 + .1,
              duration: .08, ease: 'power1.out' }, 1.4)
            .to(loader3D.root.rotation, { y: Math.PI * 2, duration: .12,
              ease: 'power2.out' }, 1.48);
        }
        loaderTimeline.play();
      });
    }

    gsap.to('#heroImg, #heroVideo', { yPercent: 10, ease: 'none',
      scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true } });
    gsap.to('.hero-inner', { yPercent: -8, opacity: .3, ease: 'none',
      scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true } });
    gsap.to('.doc-bg img', { scale: 1.13, ease: 'none',
      scrollTrigger: { trigger: '.doctrine', start: 'top bottom', end: 'bottom top', scrub: 1.2 } });

    const marquee = gsap.to('#marquee', {
      xPercent: -50, duration: 26, repeat: -1, ease: 'none'
    });
    let boost = 1;
    const marqueeTick = () => {
      const target = 1 + Math.min(Math.abs(lenis?.velocity || 0) / 6, 3.5);
      boost += (target - boost) * .06;
      marquee.timeScale(boost);
    };
    gsap.ticker.add(marqueeTick);
    cleanups.push(() => gsap.ticker.remove(marqueeTick));
    gsap.to('#manifestoText .w', { opacity: 1, stagger: .05, ease: 'none',
      scrollTrigger: { trigger: '.doctrine', start: 'top 70%', end: 'bottom 70%', scrub: true } });
    if (doctrineImages.length) {
      let index = 0;
      const timer = setInterval(() => {
        if (document.hidden) return;
        doctrineImages[index].classList.remove('on');
        index = (index + 1) % doctrineImages.length;
        doctrineImages[index].classList.add('on');
      }, 6000);
      cleanups.push(() => clearInterval(timer));
    }

    if (buckets.length) {
      const media = buckets.map(bucket => [...bucket.children]);
      const indices = buckets.map(() => 0);
      const visible = new Set();
      const sync = index => {
        media[index].forEach((element, item) => {
          const active = item === indices[index];
          element.classList.toggle('on', active);
          if (element.tagName !== 'VIDEO') return;
          if (active && visible.has(index) && !document.hidden && !disposed && !REDUCED) {
            element.play().then(() => {
              if (disposed || REDUCED || document.hidden || !visible.has(index)) element.pause();
            }).catch(() => {});
          } else element.pause();
        });
      };
      const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          const index = buckets.indexOf(entry.target);
          if (entry.isIntersecting) visible.add(index); else visible.delete(index);
          sync(index);
        });
      }, { threshold: .1 });
      buckets.forEach(bucket => observer.observe(bucket));
      const visibility = () => buckets.forEach((_, index) => sync(index));
      document.addEventListener('visibilitychange', visibility);
      const timer = setInterval(() => {
        if (document.hidden) return;
        buckets.forEach((_, index) => {
          indices[index] = (indices[index] + 1) % media[index].length;
          const next = media[index][indices[index]];
          if (next.tagName === 'VIDEO') next.currentTime = 0;
          sync(index);
        });
      }, 7000);
      cleanups.push(() => {
        observer.disconnect();
        clearInterval(timer);
        document.removeEventListener('visibilitychange', visibility);
      });
    }

    /* Create the program pin before downstream footer/image triggers. */
    const track = programTrack;
    if (track) {
      const pin = document.getElementById('programsPin');
      const getDistance = () => Math.max(0, track.scrollWidth - window.innerWidth);
      // Hidden overflow is still a native scroll container: browser focus can
      // add scrollLeft on top of the GSAP translation. Clip has the same visual
      // boundary without a competing scroll offset; reduced mode restores CSS.
      gsap.set(pin, { overflow: 'clip' });
      pin.scrollLeft = pin.scrollTop = track.scrollLeft = 0;
      const pinTween = gsap.to(track, { x: () => -getDistance(), ease: 'none',
        scrollTrigger: { trigger: '#programsPin', start: 'top top',
          end: () => '+=' + getDistance(), pin: true, scrub: 1,
          anticipatePin: 1, invalidateOnRefresh: true,
          onUpdate: self => gsap.set('#hBar', { scaleX: self.progress }) } });
      const showFocusedCard = active => {
        const card = active?.closest('.prog-card');
        if (!card || !track.contains(card) || disposed) return;
        const trigger = pinTween.scrollTrigger;
        const distance = getDistance();
        pin.scrollLeft = pin.scrollTop = track.scrollLeft = 0;
        const cardBounds = card.getBoundingClientRect();
        const cardLeft = cardBounds.left - track.getBoundingClientRect().left;
        const offset = Math.min(distance,
          Math.max(0, cardLeft - (pin.clientWidth - cardBounds.width) / 2));
        const progress = distance ? offset / distance : 0;
        const target = Math.min(trigger.end - 1, Math.max(trigger.start + 1,
          trigger.start + progress * (trigger.end - trigger.start)));
        if (lenis) lenis.scrollTo(target, { immediate: true });
        else window.scrollTo(0, target);
        ScrollTrigger.update();
        // Keyboard focus must be visible now, rather than wait for scrub: 1.
        // Wheel/reverse travel continues to use the original scrub tween.
        trigger.getTween()?.progress(1);
        pinTween.progress(trigger.progress);
      };
      const programFocus = event => {
        if (!programRestoringFocus) showFocusedCard(event.target);
      };
      revealProgramFocus = showFocusedCard;
      track.addEventListener('focusin', programFocus);
      cleanups.push(() => {
        track.removeEventListener('focusin', programFocus);
        revealProgramFocus = null;
      });
      gsap.utils.toArray('.prog-img img, .prog-img video').forEach(image => {
        gsap.fromTo(image, { yPercent: -7 }, { yPercent: 7, ease: 'none',
          scrollTrigger: { trigger: image.closest('.prog-card'), containerAnimation: pinTween,
            start: 'left right', end: 'right left', scrub: true } });
      });
    }
    gsap.fromTo('#ibImg', { yPercent: -12 }, { yPercent: 6, ease: 'none',
      scrollTrigger: { trigger: '.image-break', start: 'top bottom', end: 'bottom top', scrub: true } });
    gsap.from('.app-phone-back', { y: 54, rotation: -13, opacity: 0,
      duration: 1.1, ease: 'power3.out',
      scrollTrigger: { trigger: '.footer-app-preview', start: 'top 82%' } });
    gsap.from('.app-phone-front', { y: 72, rotation: 12, opacity: 0,
      duration: 1.1, delay: .08, ease: 'power3.out',
      scrollTrigger: { trigger: '.footer-app-preview', start: 'top 82%' } });

    return () => {
      disposed = true;
      clearTimeout(readinessTimer);
      loader3D?.dispose();
      cleanups.forEach(cleanup => cleanup());
      heroEntered = true;
      loaderFinished = true;
      staticMedia();
    };
  });
})();

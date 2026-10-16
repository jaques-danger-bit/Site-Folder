/* Homepage partner marquee. Load after home.js.
   Independent of GSAP; static roster without JS or with reduced motion. */
(() => {
  'use strict';
  const band = document.querySelector('[data-partner-marquee]');
  if (!band || !window.IntersectionObserver) return;
  const track = band.querySelector('[data-partner-track]');
  const logos = band.querySelector('[data-partner-logos]');
  const viewport = band.querySelector('.partner-marquee');
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let visible = false;

  const duplicate = logos.cloneNode(true);
  duplicate.removeAttribute('data-partner-logos');
  duplicate.classList.add('partner-logos--duplicate');
  duplicate.setAttribute('aria-hidden', 'true');
  duplicate.setAttribute('inert', '');
  duplicate.querySelectorAll('img').forEach(img => { img.alt = ''; });
  track.appendChild(duplicate);

  function update() {
    band.classList.toggle('is-animated', !motion.matches);
    band.classList.toggle('is-in-view', visible && !document.hidden);
  }
  viewport.addEventListener('pointerenter', event => {
    if (event.pointerType === 'mouse') band.classList.add('is-hovered');
  });
  viewport.addEventListener('pointerleave', () => band.classList.remove('is-hovered'));
  new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    update();
  }).observe(band);
  motion.addEventListener('change', update);
  document.addEventListener('visibilitychange', update);
  update();
})();

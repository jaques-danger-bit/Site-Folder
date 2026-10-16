/* ============================================================
   STRIKELINE — facility.js
   Home facility walkthrough. Load after GSAP + ScrollTrigger,
   BEFORE core.js/home.js so downstream triggers see the pin space.
   Static vertical chapters are the no-JS / no-library fallback.
   ============================================================ */
(() => {
  const facility = document.getElementById('facility');
  if (!facility || typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

  gsap.registerPlugin(ScrollTrigger);
  const stage = facility.querySelector('[data-facility-pin]');
  const track = facility.querySelector('[data-facility-track]');
  const progress = facility.querySelector('[data-facility-progress]');
  const exit = document.getElementById('membership-options');
  if (!stage || !track || !progress || !exit) return;

  // core.js handles anchor scrolling through Lenis. Also move keyboard focus.
  facility.querySelector('[data-facility-skip]').addEventListener('click', () => {
    exit.focus({ preventScroll: true });
  });

  const media = gsap.matchMedia();
  // The same vertical-scroll-driven walkthrough runs on phones and desktops.
  // Match home.css; compact phone panels keep copy and photos visible at 560px.
  media.add(
    '(min-height: 560px) and (prefers-reduced-motion: no-preference)',
    () => {
      facility.classList.add('facility--horizontal');
      const distance = () => Math.max(0, track.scrollWidth - stage.clientWidth);
      gsap.set(progress, { scaleX: 0 });
      gsap.to(track, {
        x: () => -distance(),
        ease: 'none',
        scrollTrigger: {
          id: 'facility-tour',
          trigger: stage,
          start: () => 'top ' + getComputedStyle(document.documentElement)
            .getPropertyValue('--nav-h').trim(),
          end: () => '+=' + distance(),
          pin: true,
          pinSpacing: true,
          scrub: .5,
          invalidateOnRefresh: true,
          // On a breakpoint change, refresh this upstream pin before the rest.
          refreshPriority: 1,
          onUpdate: self => gsap.set(progress, { scaleX: self.progress })
        }
      });

      // matchMedia reverts the tween and pin styles before restoring static flow.
      return () => facility.classList.remove('facility--horizontal');
    }
  );
})();

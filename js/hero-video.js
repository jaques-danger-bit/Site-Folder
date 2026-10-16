/* ============================================================
   STRIKELINE: hero-video.js
   Decorative hero playback and still fallback, without visible controls.
   Load after homepage markup. No library dependencies.
   ============================================================ */
(() => {
  const video = document.querySelector('[data-hero-video]');
  if (!video) return;

  const media = video.parentElement;
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let inView = false;
  let failed = false;
  let playPending = false;

  const shouldPlay = () => !motion.matches && inView && !document.hidden && !failed;

  const syncPlayback = () => {
    if (motion.matches) media.classList.remove('has-video');
    if (!shouldPlay()) {
      video.pause();
      return;
    }
    // No video request for reduced-motion or no-JS visitors; the image stays visible.
    if (!video.hasAttribute('src')) {
      video.muted = true;
      video.src = video.dataset.src;
    }
    if (!playPending && video.paused) {
      playPending = true;
      video.play().catch(() => {
        // Autoplay may be blocked by the browser. Keep the equipment still visible.
      }).finally(() => {
        playPending = false;
        if (!shouldPlay()) video.pause();
      });
    }
  };

  video.addEventListener('playing', () => {
    if (shouldPlay()) media.classList.add('has-video');
    else video.pause();
  });
  video.addEventListener('error', () => {
    failed = true;
    media.classList.remove('has-video');
    video.pause();
  });
  motion.addEventListener('change', syncPlayback);
  document.addEventListener('visibilitychange', syncPlayback);
  new IntersectionObserver(entries => {
    inView = entries[0].isIntersecting;
    syncPlayback();
  }, { threshold: 0 }).observe(media);
})();

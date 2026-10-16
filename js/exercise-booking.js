/* ============================================================
   STRIKELINE — exercise-booking.js
   Memberships: select a class in the visible native booking frame. Load after
   core.js and expanders.js; independent of animation libraries.
   ============================================================ */
(() => {
  const panel = document.querySelector('[data-exercise-panel]');
  if (!panel) return;
  const heading = panel.querySelector('[data-exercise-heading]');
  const fallback = panel.querySelector('[data-exercise-fallback]');
  const frame = panel.querySelector('iframe');

  document.querySelectorAll('[data-exercise-booking]').forEach(link => {
    link.addEventListener('click', event => {
      if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey ||
          event.shiftKey || event.altKey || link.target === '_blank') return;
      event.preventDefault();
      heading.textContent = link.dataset.exerciseBooking;
      fallback.href = link.href;
      frame.title = `Strikeline booking: ${link.dataset.exerciseBooking}`;
      frame.src = `${link.href}&embedded=true&iframe=true&web_embed=true`;
      heading.focus({ preventScroll: true });
      panel.scrollIntoView({ block: 'start', behavior: 'instant' });
    });
  });
})();

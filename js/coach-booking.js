/* ============================================================
   STRIKELINE — coach-booking.js
   About: on-demand native Exercise.com booking. Load after core.js
   and expanders.js; independent of animation libraries.
   ============================================================ */
(() => {
  const panel = document.querySelector('[data-booking-panel]');
  if (!panel) return;
  const heading = panel.querySelector('[data-booking-heading]');
  const fallback = panel.querySelector('[data-booking-fallback]');
  const host = panel.querySelector('[data-booking-frame]');
  let selectedLink;

  document.querySelectorAll('[data-coach-booking]').forEach(link => {
    link.addEventListener('click', event => {
      if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey ||
          event.shiftKey || event.altKey || link.target === '_blank') return;
      event.preventDefault();
      selectedLink = link;
      const coach = link.dataset.coachBooking;
      const standalone = link.href;
      const action = link.dataset.bookingService || 'Book';
      heading.textContent = `${action} with ${coach}`;
      fallback.href = standalone;
      const frame = document.createElement('iframe');
      frame.title = `Strikeline ${action.toLowerCase()} with ${coach}`;
      frame.src = `${standalone}&embedded=true&iframe=true&web_embed=true`;
      host.replaceChildren(frame);
      panel.hidden = false;
      heading.focus({ preventScroll: true });
      panel.scrollIntoView({ block: 'start', behavior: 'instant' });
    });
  });

  panel.querySelector('[data-booking-close]').addEventListener('click', () => {
    host.replaceChildren();
    panel.hidden = true;
    selectedLink?.focus();
  });
})();

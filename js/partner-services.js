/* STRIKELINE — partner pop-up inquiry selection. Load after contact.js.
   Native anchors and the required select remain usable without JavaScript. */
(function () {
  'use strict';

  const form = document.getElementById('contactForm');
  const select = document.getElementById('popup-service');
  if (!form || !select) return;

  document.querySelectorAll('[data-service-interest]').forEach(link => {
    link.addEventListener('click', () => {
      if (select.disabled) return;
      const option = Array.from(select.options).find(item =>
        item.dataset.service === link.dataset.serviceInterest);
      if (!option) return;
      select.value = option.value;
      select.dispatchEvent(new Event('change', { bubbles: true }));
      select.focus({ preventScroll: true });
    });
  });
}());

/* STRIKELINE — Contact and partner-services delivery. Loads after core.js, but needs no animation libraries.
   Native HTML POST remains the fallback when JavaScript or fetch is unavailable. */
(function () {
  'use strict';

  const form = document.getElementById('contactForm');
  if (!form || !window.fetch || !window.FormData || !window.AbortController) return;

  const status = form.querySelector('[data-contact-status]');
  const button = form.querySelector('button[type="submit"]');
  const label = button.querySelector('span');
  const idleLabel = label.textContent;
  const controls = Array.from(form.elements);
  const partnerInquiry = !!form.querySelector('[name="service_interest"]');
  let pending = false;
  let sent = false;

  function show(state, message) {
    status.dataset.state = state;
    status.textContent = message;
    if (state === 'success') {
      const link = document.createElement('a');
      link.setAttribute('href', 'tel:+18542088025');
      link.setAttribute('data-form-next', '');
      link.textContent = 'Call the Gym';
      const nextStep = partnerInquiry
        ? ' For pop-up questions: '
        : ' You can also contact us by phone: ';
      status.append(document.createTextNode(nextStep), link);
    }
  }

  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    if (pending || sent) return;
    if (!form.reportValidity()) return;

    // Capture values before disabling fields so pending edits cannot change the sent message.
    const body = new FormData(form);
    const disabled = controls.map((control) => control.disabled);
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 20000);
    pending = true;
    form.setAttribute('aria-busy', 'true');
    controls.forEach((control) => {
      control.disabled = true;
    });
    label.textContent = 'Sending...';
    show('pending', 'Sending your message...');

    try {
      const response = await fetch(form.action, {
        method: 'POST',
        body,
        headers: { Accept: 'application/json' },
        signal: controller.signal,
      });
      const result = await response.json().catch(() => null);

      if (response.ok && result && result.ok === true) {
        sent = true;
        label.textContent = 'Message Sent';
        show(
          'success',
          form.dataset.successMessage || 'Message sent. Thank you for contacting Strikeline.',
        );
      } else if (response.status === 429) {
        show(
          'error',
          'Too many attempts. Please wait a few minutes before trying again, ' +
            'or email info@strikelinetraining.com.',
        );
      } else if (response.ok) {
        show(
          'error',
          'We could not confirm delivery. Please wait before retrying, ' +
            'or email info@strikelinetraining.com.',
        );
      } else {
        show(
          'error',
          'Your message could not be sent. Please check your details and try again, ' +
            'or email info@strikelinetraining.com.',
        );
      }
    } catch (error) {
      // A lost response does not prove the server rejected the message. Never auto-retry.
      show(
        'error',
        'We could not confirm delivery. Your message is still here. ' +
          'Please wait before retrying, or email info@strikelinetraining.com.',
      );
    } finally {
      window.clearTimeout(timeout);
      pending = false;
      form.setAttribute('aria-busy', 'false');
      if (!sent) {
        controls.forEach((control, index) => {
          control.disabled = disabled[index];
        });
        label.textContent = idleLabel;
      }
    }
  });
})();

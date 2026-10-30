/* Coach landing pages: Formspree receipt first, then the coach's booking link.
   No browser persistence, automatic retries, booking submissions, or DM sends. */
(function () {
  'use strict';

  const ENDPOINT = 'https://formspree.io/f/mdajqedj';
  const COACHES = new Set(['Justin', 'Zach', 'Rhylie']);
  const UTM_KEYS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'];
  const supported = window.fetch && window.FormData && window.AbortController;

  function makeId() {
    if (window.crypto && typeof window.crypto.randomUUID === 'function') return window.crypto.randomUUID();
    return Date.now().toString(36) + '-' + Math.random().toString(36).slice(2)
      + '-' + Math.random().toString(36).slice(2);
  }

  function initialize() {
    document.querySelectorAll('.stg-coach-page').forEach(root => {
      const coach = root.dataset.coach;
      const form = root.querySelector('form[data-coach-intake]');
      const success = root.querySelector('[data-intake-success]');
      if (!COACHES.has(coach) || !form || !success || form.dataset.intakeBound) return;
      const status = form.querySelector('[data-form-status]') || root.querySelector('[data-form-status]');
      const button = form.querySelector('button[type="submit"]');
      if (!status || !button) return;
      form.dataset.intakeBound = 'true';

      const sticky = root.querySelector('[data-sticky-cta]');
      if (sticky && 'IntersectionObserver' in window) {
        sticky.hidden = true;
        const targets = [root.querySelector('.stg-hero'), form].filter(Boolean);
        const visible = new Map(targets.map(target => [target, false]));
        const observer = new IntersectionObserver(entries => {
          entries.forEach(entry => visible.set(entry.target, entry.isIntersecting));
          sticky.hidden = Array.from(visible.values()).some(Boolean) || !success.hidden;
        }, { threshold: 0 });
        targets.forEach(target => observer.observe(target));
      }

      // Without these APIs the markup retains its native Formspree POST fallback.
      if (!supported) return;
      const source = form.elements.namedItem('source')?.value || '';
      const subject = form.elements.namedItem('_subject')?.value || '';
      const originalLabel = button.textContent;
      const submissionId = makeId();
      const params = new URLSearchParams(window.location.search);
      const campaign = {};
      UTM_KEYS.forEach(key => {
        const value = (params.get(key) || '').replace(/[\u0000-\u001f\u007f]/g, '').trim().slice(0, 120);
        if (value) campaign[key] = value;
      });
      let pending = false;
      let sent = false;

      function announce(state, message) {
        status.dataset.state = state;
        status.textContent = message;
      }

      form.addEventListener('submit', async event => {
        event.preventDefault();
        if (pending || sent || !form.reportValidity()) return;
        if (form.action !== ENDPOINT || !source) {
          announce('error', 'This form is not ready to send. Please use the contact link below.');
          return;
        }

        // Construct the payload before disabling controls. Never read routing from the query string.
        const body = new FormData(form);
        body.set('coach', coach);
        body.set('source', source);
        body.set('_subject', subject);
        body.set('submission_id', submissionId);
        UTM_KEYS.forEach(key => {
          body.delete(key);
          if (campaign[key]) body.set(key, campaign[key]);
        });
        const controls = Array.from(form.elements);
        const wasDisabled = controls.map(control => control.disabled);
        pending = true;
        controls.forEach(control => { control.disabled = true; });
        form.setAttribute('aria-busy', 'true');
        button.textContent = 'Sending your details…';
        announce('pending', 'Sending your details…');

        const controller = new AbortController();
        const timer = window.setTimeout(() => controller.abort(), 20000);
        let message = 'We couldn’t confirm delivery. Your answers are still here. Please wait a moment before trying again.';
        try {
          const response = await fetch(ENDPOINT, {
            method: 'POST', body,
            headers: { Accept: 'application/json' },
            credentials: 'omit', signal: controller.signal
          });
          const result = await response.json().catch(() => null);
          if (response.ok && result && result.ok === true) {
            sent = true;
          } else if (response.status === 429) {
            message = 'Too many attempts. Your answers are still here. Please wait a few minutes before trying again.';
          } else if (!response.ok) {
            message = 'Your details weren’t accepted. Your answers are still here. Check them and try again.';
          }
        } catch (_) {
          // The server may have received a timed-out request. Leave any retry to the visitor.
        } finally {
          window.clearTimeout(timer);
          pending = false;
          form.setAttribute('aria-busy', 'false');
        }

        if (sent) {
          announce('success', 'Your details were received. Choose a time to talk with ' + coach + '.');
          button.textContent = 'Details received';
          button.hidden = true;
          const fields = form.querySelector('[data-form-fields]');
          if (fields) fields.hidden = true;
          success.hidden = false;
          if (sticky) sticky.hidden = true;
          const heading = success.querySelector('h3, [tabindex="-1"]');
          if (heading) heading.focus({ preventScroll: true });
          success.scrollIntoView({ block: 'nearest', behavior: 'auto' });
          root.dispatchEvent(new CustomEvent('stg:intake-success', {
            bubbles: true, detail: { coach, submission_id: submissionId }
          }));
        } else {
          controls.forEach((control, index) => { control.disabled = wasDisabled[index]; });
          button.textContent = originalLabel;
          announce('error', message);
        }
      });
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize, { once: true });
  else initialize();
}());

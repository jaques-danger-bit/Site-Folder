/* STRIKELINE — public form delivery. Load before page scripts; no animation dependencies.
   Formspree is the submission gateway. Confirmation means accepted there, not imported to the portal.
   Native POST remains available without JS. Answers stay in memory only, never browser storage. */
(function () {
  'use strict';

  const supported = window.fetch && window.FormData && window.AbortController;
  const fallback = 'Please wait before retrying, or call (770) 862-8942.';

  function submissionId() {
    if (window.crypto && window.crypto.randomUUID) return window.crypto.randomUUID();
    return Date.now().toString(36) + '-' + Math.random().toString(36).slice(2)
      + '-' + Math.random().toString(36).slice(2);
  }

  async function deliver(url, body) {
    if (!supported) return { state: 'error', message: 'Online delivery is unavailable. ' + fallback };
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 20000);
    try {
      const headers = { Accept: 'application/json' };
      if (!(body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
        body = JSON.stringify(body);
      }
      const response = await fetch(url, { method: 'POST', body, headers, signal: controller.signal });
      const result = await response.json().catch(() => null);
      if (response.ok && result && result.ok === true) {
        return { state: 'success', message: 'Submission received. Thank you.' };
      }
      if (response.status === 429) {
        return { state: 'error', message: 'Too many attempts. Please wait a few minutes, '
          + 'then try again, or call (770) 862-8942.' };
      }
      if (!response.ok) {
        return { state: 'error', message: 'Your submission was not accepted. '
          + 'Your answers are still here. Please check your details and try again, '
          + 'or call (770) 862-8942.' };
      }
    } catch (_) {
      // A timeout or lost response may occur after acceptance. Never automatically resubmit.
    } finally { window.clearTimeout(timeout); }
    return { state: 'error', message: 'We could not confirm delivery. Your answers are still here. '
      + fallback };
  }

  function show(status, state, message, nextAction) {
    status.dataset.state = state;
    status.textContent = message;
    if (nextAction) {
      const link = document.createElement('a');
      link.setAttribute('href', nextAction.href);
      link.setAttribute('data-form-next', '');
      link.textContent = nextAction.label;
      status.append(document.createTextNode(' '), link);
    }
  }

  // One completed quiz payload, with an explicit retry that keeps the same submission identifier.
  function submitQuiz(host, url, payload) {
    const panel = document.createElement('div');
    panel.className = 'form-delivery';
    const status = document.createElement('p');
    status.className = 'form-status';
    status.setAttribute('data-form-status', '');
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    status.setAttribute('aria-atomic', 'true');
    const retry = document.createElement('button');
    retry.type = 'button';
    retry.className = 'btn';
    retry.textContent = 'Retry Sending';
    retry.setAttribute('data-form-retry', '');
    retry.hidden = true;
    panel.append(status, retry);
    host.append(panel);
    const body = { ...payload, submission_id: submissionId() };
    let pending = false;
    let sent = false;
    async function send() {
      if (pending || sent) return;
      pending = true;
      retry.hidden = true;
      retry.disabled = true;
      panel.setAttribute('aria-busy', 'true');
      show(status, 'pending', 'Sending your results to Strikeline...');
      const result = await deliver(url, body);
      sent = result.state === 'success';
      show(status, result.state, sent ? 'Your results were sent to Strikeline.' : result.message);
      pending = false;
      panel.setAttribute('aria-busy', 'false');
      retry.disabled = false;
      retry.hidden = sent;
    }
    retry.addEventListener('click', send);
    send();
  }

  window.STGForms = { submitQuiz };
  if (!supported) return;
  document.querySelectorAll('form[data-form-delivery]').forEach(form => {
    const status = form.querySelector('[data-form-status]');
    const button = form.querySelector('button[type="submit"]');
    if (!status || !button) return;
    const label = button.querySelector('span') || button;
    const originalLabel = label.textContent;
    const controls = Array.from(form.elements);
    const assessment = form.id === 'applyForm';
    const id = submissionId();
    let pending = false;
    let sent = false;
    form.addEventListener('submit', async event => {
      event.preventDefault();
      if (pending || sent || !form.reportValidity()) return;
      const body = new FormData(form);
      body.set('submission_id', id);
      const disabled = controls.map(control => control.disabled);
      pending = true;
      form.setAttribute('aria-busy', 'true');
      controls.forEach(control => { control.disabled = true; });
      label.textContent = 'Sending...';
      show(status, 'pending', 'Sending your submission...');
      const result = await deliver(form.action, body);
      sent = result.state === 'success';
      const message = sent ? form.dataset.successMessage || (assessment
        ? 'Your training inquiry was sent to Strikeline. For coaching and intro-call options:'
        : result.message) : result.message;
      show(status, result.state, message, sent && assessment ? {
        href: 'about.html#coaches', label: 'Meet the Coaches',
      } : null);
      pending = false;
      form.setAttribute('aria-busy', 'false');
      if (sent) label.textContent = assessment ? 'Inquiry Sent' : 'Submission Received';
      else {
        controls.forEach((control, index) => { control.disabled = disabled[index]; });
        label.textContent = originalLabel;
      }
    });
  });
}());

/* Dialogs enhance real checkout links; this code does not handle payment or fulfillment state. */
(() => {
  'use strict';
  const stripeSource = 'https://js.stripe.com/v3/buy-button.js';
  function loadStripe() {
    if (customElements.get('stripe-buy-button')) return Promise.resolve();
    if (window.__stgBuyButtonLoader) return window.__stgBuyButtonLoader;
    window.__stgBuyButtonLoader = new Promise((resolve, reject) => {
      let settled = false;
      const finish = error => {
        if (settled) return;
        settled = true;
        clearTimeout(timeout);
        error ? reject(error) : resolve();
      };
      const timeout = setTimeout(() => finish(new Error('Stripe did not become available.')), 12000);
      let script = Array.from(document.scripts).find(item => item.src === stripeSource);
      if (!script) {
        script = document.createElement('script');
        script.src = stripeSource;
        script.async = true;
        script.dataset.stripeBuyButtonLoader = '';
        script.addEventListener('error', () => finish(new Error('Stripe could not load.')), { once: true });
        document.head.appendChild(script);
      } else {
        script.addEventListener('error', () => finish(new Error('Stripe could not load.')), { once: true });
      }
      customElements.whenDefined('stripe-buy-button').then(() => finish());
    });
    return window.__stgBuyButtonLoader;
  }
  document.querySelectorAll('[data-purchase-page]').forEach(page => {
    if (page.dataset.purchaseReady) return;
    page.dataset.purchaseReady = 'true';
    const dialog = page.querySelector('[data-checkout-dialog]');
    const configElement = page.querySelector('[data-purchase-config]');
    if (!dialog || !configElement || typeof dialog.showModal !== 'function' || !window.customElements) return;
    let config;
    try { config = JSON.parse(configElement.textContent); } catch { return; }
    const offers = new Map(config.offers.map(offer => [offer.slug, offer]));
    const mount = dialog.querySelector('[data-purchase-embed]');
    const status = dialog.querySelector('[data-checkout-status]');
    const closeButton = dialog.querySelector('[data-checkout-close]');
    let opener = null;
    let previousOverflow = '';
    let openVersion = 0;
    page.querySelectorAll('[data-open-checkout]').forEach(link => {
      link.addEventListener('click', async event => {
        if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        const offer = offers.get(link.dataset.openCheckout);
        if (!offer) return;
        event.preventDefault();
        opener = link;
        const version = ++openVersion;
        dialog.querySelector('[data-checkout-title]').textContent = offer.name;
        dialog.querySelector('[data-checkout-details]').textContent = `${offer.price} ${offer.cadence} · USD`;
        dialog.querySelector('[data-checkout-terms]').textContent = offer.terms;
        dialog.querySelector('[data-checkout-fallback]').href = offer.checkoutUrl;
        dialog.dataset.activeOffer = offer.slug;
        dialog.dataset.clientReferenceId = offer.reference;
        status.textContent = 'Loading secure checkout…';
        delete status.dataset.state;
        mount.replaceChildren();
        previousOverflow = document.body.style.overflow;
        document.body.style.overflow = 'hidden';
        dialog.showModal();
        closeButton.focus({ preventScroll: true });
        try {
          await loadStripe();
          if (!dialog.open || version !== openVersion) return;
          const button = document.createElement('stripe-buy-button');
          button.setAttribute('buy-button-id', offer.buttonId);
          button.setAttribute('publishable-key', config.publishableKey);
          button.setAttribute('client-reference-id', offer.reference);
          mount.replaceChildren(button);
          status.textContent = 'Use the Stripe form below, or open secure checkout directly.';
        } catch {
          if (!dialog.open || version !== openVersion) return;
          status.textContent = 'The embedded checkout could not load. Use the secure checkout link below to continue.';
          status.dataset.state = 'error';
        }
      });
    });
    closeButton.addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', event => {
      if (event.target !== dialog) return;
      const bounds = dialog.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
    });
    dialog.addEventListener('close', () => {
      ++openVersion;
      document.body.style.overflow = previousOverflow;
      mount.replaceChildren();
      if (opener && opener.isConnected) opener.focus({ preventScroll: true });
    });
  });
})();

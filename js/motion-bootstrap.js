/* STRIKELINE — bounded animation startup on every page.
   Load last, after inert library/app declarations. Keep their DOM order; essential
   local behavior starts even if an optional CDN request never finishes. */
(function () {
  'use strict';

  const BUDGET = 1800;
  const declarations = selector => Array.from(document.querySelectorAll(selector));

  function libraries(items) {
    return new Promise(resolve => {
      let settled = false;
      let index = 0;
      const finish = ready => {
        if (settled) return;
        settled = true;
        clearTimeout(deadline);
        resolve(ready);
      };
      const deadline = setTimeout(() => finish(false), BUDGET);
      const next = () => {
        if (settled) return;
        const item = items[index++];
        if (!item) { finish(true); return; }
        const script = document.createElement('script');
        script.async = true;
        script.src = item.dataset.src;
        script.onload = next;
        script.onerror = () => finish(false);
        document.head.appendChild(script);
      };
      next();
    });
  }

  function localScript(item) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      if (item.dataset.src) {
        script.async = false;
        script.src = item.dataset.src;
        script.onload = resolve;
        script.onerror = () => reject(new Error('Local script unavailable: ' + item.dataset.src));
      } else script.textContent = item.textContent;
      document.body.appendChild(script);
      if (!item.dataset.src) resolve();
    });
  }

  // THREE then SVGLoader run independently of essential site startup. A late
  // completion cannot extend either deadline or start another dependency.
  const shield = declarations('script[data-shield-library]');
  if (shield.length) {
    window.strikelineShieldLoaderReady = libraries(shield).then(ready =>
      ready && typeof window.THREE?.SVGLoader === 'function');
  }

  window.strikelineSiteReady = (async () => {
    window.strikelineMotionLibrariesReady =
      await libraries(declarations('script[data-motion-library]'));
    for (const item of declarations('script[data-site-script]')) await localScript(item);
    document.documentElement.setAttribute('data-site-ready', 'true');
    return true;
  })().catch(error => {
    // Preserve native content and links if a required local file is unavailable.
    document.documentElement.classList.remove('js');
    document.documentElement.classList.add('reduced', 'motion-unavailable');
    document.getElementById('preloader')?.style.setProperty('display', 'none');
    console.error(error);
    return false;
  });
}());

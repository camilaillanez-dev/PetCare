(() => {
  const menuToggle = document.getElementById('menu-toggle');
  const navLinks = document.getElementById('nav-links');

  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', () => {
      const isOpen = navLinks.classList.toggle('open');
      menuToggle.setAttribute('aria-expanded', String(isOpen));
      menuToggle.setAttribute('aria-label', isOpen ? 'Cerrar menú' : 'Abrir menú');
    });

    navLinks.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => {
        navLinks.classList.remove('open');
        menuToggle.setAttribute('aria-expanded', 'false');
        menuToggle.setAttribute('aria-label', 'Abrir menú');
      });
    });
  }

  const dogEyes = document.getElementById('dog-eyes');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (!dogEyes || reduceMotion.matches) return;

  let targetX = 0;
  let targetY = 0;
  let currentX = 0;
  let currentY = 0;
  let frameId = 0;

  function animateEyes() {
    frameId = 0;
    if (document.hidden || reduceMotion.matches) return;
    currentX += (targetX - currentX) * 0.12;
    currentY += (targetY - currentY) * 0.12;
    dogEyes.style.transform = `translate3d(${currentX.toFixed(2)}px, ${currentY.toFixed(2)}px, 0)`;

    if (Math.abs(targetX - currentX) > 0.03 || Math.abs(targetY - currentY) > 0.03) {
      frameId = window.requestAnimationFrame(animateEyes);
    }
  }

  window.addEventListener('pointermove', (event) => {
    const nx = (event.clientX / window.innerWidth - 0.5) * 2;
    const ny = (event.clientY / window.innerHeight - 0.5) * 2;
    targetX = Math.max(-4.5, Math.min(4.5, nx * 4.5));
    targetY = Math.max(-3.5, Math.min(3.5, ny * 3.5));
    if (!frameId) frameId = window.requestAnimationFrame(animateEyes);
  }, { passive: true });

  document.addEventListener('visibilitychange', () => {
    if (document.hidden && frameId) {
      window.cancelAnimationFrame(frameId);
      frameId = 0;
    }
  });

  reduceMotion.addEventListener?.('change', () => {
    if (reduceMotion.matches && frameId) {
      window.cancelAnimationFrame(frameId);
      frameId = 0;
    }
  });
})();

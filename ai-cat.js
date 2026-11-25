(() => {
  const path = window.location.pathname;
  const context = path.includes('clinic')
    ? 'clinic'
    : path.includes('portal')
      ? 'portal'
      : 'public';

  const container = document.createElement('div');
  container.className = 'ai-cat-widget';
  container.id = 'ai-cat-widget';
  container.innerHTML = `
    <div class="ai-cat-panel" id="ai-cat-panel" role="dialog" aria-label="Asistente virtual PetCare" aria-modal="false" aria-labelledby="ai-cat-title" hidden>
      <div class="ai-cat-header">
        <div class="ai-cat-identity">
          <span class="ai-cat-dot" aria-hidden="true"></span>
          <div>
            <b id="ai-cat-title">Asistente Felino · PetCare</b>
            <small>Orientación formal en línea</small>
          </div>
        </div>
        <div class="ai-cat-controls">
          <button type="button" id="ai-voice-toggle" class="ai-icon-btn" title="Activar o silenciar voz" aria-label="Activar o silenciar voz">🔊</button>
          <button type="button" id="ai-cat-close" class="ai-icon-btn" aria-label="Cerrar asistente">✕</button>
        </div>
      </div>

      <div class="ai-cat-messages" id="ai-cat-messages" aria-live="polite">
        <div class="ai-msg ai-msg-bot">${getWelcomeMessage(context)}</div>
      </div>

      <div class="ai-cat-chips" id="ai-cat-chips">${getQuickChips(context)}</div>

      <form class="ai-cat-form" id="ai-cat-form">
        <input type="text" id="ai-cat-input" placeholder="Escriba su consulta aquí..." autocomplete="off" required>
        <button type="submit" aria-label="Enviar consulta">→</button>
      </form>
    </div>

    <button type="button" class="ai-cat-bubble" id="ai-cat-bubble">
      Mis respetos. ¿Necesita orientación?
    </button>

    <button type="button" class="ai-cat-trigger" id="ai-cat-trigger" aria-label="Abrir asistente virtual" aria-controls="ai-cat-panel" aria-expanded="false">
      <svg class="cat-avatar-svg" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <path d="M18 34 L14 12 L34 24 Z" fill="var(--bg-pure, #fff)" stroke="var(--ink, #1f2937)" stroke-width="2.5" stroke-linejoin="round"/>
        <path d="M62 34 L66 12 L46 24 Z" fill="var(--bg-pure, #fff)" stroke="var(--ink, #1f2937)" stroke-width="2.5" stroke-linejoin="round"/>
        <path d="M20 30 L18 18 L29 25 Z" fill="#93c5fd" opacity="0.6"/>
        <path d="M60 30 L62 18 L51 25 Z" fill="#93c5fd" opacity="0.6"/>
        <rect x="14" y="22" width="52" height="42" rx="21" fill="var(--bg-pure, #fff)" stroke="var(--ink, #1f2937)" stroke-width="2.5"/>
        <g class="cat-eyes">
          <circle cx="30" cy="41" r="3.5" fill="var(--ink, #1f2937)"/>
          <circle cx="50" cy="41" r="3.5" fill="var(--ink, #1f2937)"/>
          <circle cx="31" cy="39.8" r="1.1" fill="#ffffff"/>
          <circle cx="51" cy="39.8" r="1.1" fill="#ffffff"/>
        </g>
        <path d="M38 47 L42 47 L40 49.5 Z" fill="#3b82f6"/>
        <path class="cat-mouth" d="M36 52 Q40 54.5 44 52" stroke="var(--ink, #1f2937)" stroke-width="2" stroke-linecap="round"/>
        <line x1="10" y1="44" x2="21" y2="45" stroke="var(--ink, #1f2937)" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
        <line x1="10" y1="49" x2="21" y2="48" stroke="var(--ink, #1f2937)" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
        <line x1="70" y1="44" x2="59" y2="45" stroke="var(--ink, #1f2937)" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
        <line x1="70" y1="49" x2="59" y2="48" stroke="var(--ink, #1f2937)" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
        <path d="M32 63 L40 66 L32 69 Z" fill="#3b82f6"/>
        <path d="M48 63 L40 66 L48 69 Z" fill="#3b82f6"/>
        <circle cx="40" cy="66" r="2.2" fill="#1d4ed8"/>
      </svg>
    </button>
  `;
  document.body.appendChild(container);

  function getWelcomeMessage(ctx) {
    if (ctx === 'clinic') {
      return 'Estimado/a integrante del equipo clínico, sea usted bienvenido/a. Estoy a su disposición para orientarle sobre duraciones de agenda, notas SOAP, control de stock o alertas prioritarias.';
    }
    if (ctx === 'portal') {
      return 'Estimado/a tutor/a, bienvenido/a a su Portal PetCare. Puedo asistirle con la solicitud de turnos, la instalación de la app en su dispositivo o la consulta de su historial compartido.';
    }
    return 'Estimado/a visitante, sea usted muy bienvenido/a a PetCare. Estoy a su entera disposición para orientarle sobre el acceso de demostración, la instalación de la app o el funcionamiento de la plataforma.';
  }

  function getQuickChips(ctx) {
    if (ctx === 'clinic') {
      return `
        <button type="button" data-q="¿Cuáles son las duraciones de los turnos?">Duraciones de agenda</button>
        <button type="button" data-q="¿Qué ve el tutor en su historial?">Privacidad SOAP</button>
        <button type="button" data-q="¿Cómo funciona el stock?">Control de stock</button>
      `;
    }
    return `
      <button type="button" data-q="¿Cuáles son los datos de acceso demo?">Cuenta demo</button>
      <button type="button" data-q="¿Cómo instalo la app en mi celular?">Instalar app (PWA)</button>
      <button type="button" data-q="¿Cómo pido un turno o teleconsulta?">Turnos y teleconsulta</button>
      <button type="button" data-q="Tengo una emergencia veterinaria">Emergencia</button>
    `;
  }

  const panel = document.getElementById('ai-cat-panel');
  const trigger = document.getElementById('ai-cat-trigger');
  const bubble = document.getElementById('ai-cat-bubble');
  const closeBtn = document.getElementById('ai-cat-close');
  const voiceBtn = document.getElementById('ai-voice-toggle');
  const messagesBox = document.getElementById('ai-cat-messages');
  const form = document.getElementById('ai-cat-form');
  const input = document.getElementById('ai-cat-input');
  const chips = document.getElementById('ai-cat-chips');

  let voiceEnabled = true;

  function speak(text) {
    if (!voiceEnabled || !('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'es-AR';
    utterance.rate = 0.96;
    utterance.pitch = 1.05;

    utterance.onstart = () => container.classList.add('is-speaking');
    utterance.onend = () => container.classList.remove('is-speaking');
    utterance.onerror = () => container.classList.remove('is-speaking');

    window.speechSynthesis.speak(utterance);
  }

  function getFormalResponse(rawText) {
    const q = rawText.toLowerCase();

    if (q.includes('urgencia') || q.includes('emergencia') || q.includes('guardia') || q.includes('veneno') || q.includes('intoxicación') || q.includes('no respira') || q.includes('sangrado')) {
      return 'Si su mascota puede estar en una emergencia, llame ahora a su clínica o acuda a una guardia veterinaria. En PetCare, la opción “Emergencia” genera una alerta prioritaria inmediata; no espere una respuesta del chat ni la confirmación de un turno.';
    }
    if (q.includes('dosis') || q.includes('medicamento') || q.includes('medicación') || q.includes('síntoma') || q.includes('sintoma') || q.includes('vomit') || q.includes('dolor') || q.includes('diagnóstico') || q.includes('diagnostico')) {
      return 'No puedo evaluar síntomas, indicar diagnósticos ni recomendar medicamentos o dosis. Para cuidar a su mascota, consulte con un/a profesional veterinario/a. Si los síntomas son graves o empeoran, llame ahora a su clínica o acuda a una guardia.';
    }
    if (q.includes('demo') || q.includes('usuario') || q.includes('contraseña') || q.includes('cuenta') || q.includes('vincular')) {
      return 'Para ingresar con la cuenta de demostración del portal, utilice el correo carlos.ruiz@petcare.demo y la contraseña bienvenida2026. Si crea una cuenta nueva y su teléfono coincide con una ficha de la clínica, sus mascotas se vincularán automáticamente.';
    }
    if (q.includes('instalar') || q.includes('pwa') || q.includes('celular') || q.includes('iphone') || q.includes('android') || q.includes('offline')) {
      return 'PetCare es una aplicación instalable (PWA). En Chrome o Edge seleccione "Instalar PetCare"; en Safari (iPhone/iPad) pulse Compartir y luego "Agregar a pantalla de inicio". El modo sin conexión conserva la interfaz, aunque consultar o pedir turnos requiere conexión con el servidor.';
    }
    if (q.includes('duracion') || q.includes('duración') || q.includes('tiempo') || q.includes('minuto')) {
      return 'Las duraciones iniciales en la agenda clínica son: vacunación (15 min), control (20 min), teleconsulta (25 min), consulta general (30 min), estudio diagnóstico (45 min) y procedimiento (60 min). El equipo puede ajustar estos tiempos al crear cada turno.';
    }
    if (q.includes('soap') || q.includes('borrador') || q.includes('privacidad') || q.includes('historial') || q.includes('compartido')) {
      return 'En el historial del tutor únicamente son visibles los registros que la clínica marca expresamente como compartidos. Los borradores SOAP y notas internas permanecen privados dentro del panel clínico.';
    }
    if (q.includes('teleconsulta') || q.includes('video') || q.includes('videollamada')) {
      return 'Puede solicitar una teleconsulta (25 min) desde el portal eligiendo horario disponible; quedará pendiente hasta que la clínica la confirme. Le informo con transparencia que la sala de videollamada aún requiere integración externa posterior.';
    }
    if (q.includes('turno') || q.includes('cita') || q.includes('calendario') || q.includes('recordatorio')) {
      return 'Desde el Portal de Tutores puede solicitar consultas eligiendo horarios libres (quedan pendientes de confirmación clínica) y gestionar su calendario familiar con recordatorios personales de vacunas o medicación.';
    }
    if (q.includes('stock') || q.includes('inventario') || q.includes('vencimiento')) {
      return 'El módulo de Stock del panel clínico controla existencias mínimas, fechas de vencimiento y mantiene un historial auditable de cada entrada, salida y ajuste de saldo.';
    }
    if (q.includes('servidor') || q.includes('iniciar') || q.includes('sqlite') || q.includes('seguridad')) {
      return 'En entorno local (Windows), se inicia ejecutando "Iniciar PetCare.bat" o "python server.py" en 127.0.0.1:8765, generando la base data/petcare.sqlite3 con datos ficticios. Para uso productivo requiere despliegue HTTPS, respaldos y control de roles.';
    }
    if (q.includes('hola') || q.includes('buen') || q.includes('gracias')) {
      return 'Es un verdadero honor asistirle. Estoy a su disposición para resolver dudas sobre turnos, cuenta demo, instalación en dispositivos móviles o gestión clínica.';
    }

    return 'Agradezco su consulta. Puedo orientarle con precisión sobre: la cuenta demo (carlos.ruiz@petcare.demo), instalación de la app en celular, solicitud de turnos, privacidad de notas SOAP, duraciones de agenda o protocolo de emergencias.';
  }

  function appendMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `ai-msg ${sender === 'user' ? 'ai-msg-user' : 'ai-msg-bot'}`;
    div.textContent = text;
    messagesBox.appendChild(div);
    messagesBox.scrollTop = messagesBox.scrollHeight;
  }

  function handleUserQuery(text) {
    const clean = text.trim();
    if (!clean) return;
    appendMessage(clean, 'user');

    setTimeout(() => {
      const reply = getFormalResponse(clean);
      appendMessage(reply, 'bot');
      speak(reply);
    }, 260);
  }

  function togglePanel(forceOpen) {
    const isOpen = typeof forceOpen === 'boolean' ? forceOpen : panel.hidden;
    panel.hidden = !isOpen;
    trigger.setAttribute('aria-expanded', String(isOpen));
    if (isOpen) {
      bubble.hidden = true;
      input.focus();
    } else if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      container.classList.remove('is-speaking');
    }
  }

  trigger.addEventListener('click', () => togglePanel());
  bubble.addEventListener('click', () => togglePanel(true));
  closeBtn.addEventListener('click', () => togglePanel(false));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !panel.hidden) {
      togglePanel(false);
      trigger.focus();
    }
  });

  voiceBtn.addEventListener('click', () => {
    voiceEnabled = !voiceEnabled;
    voiceBtn.textContent = voiceEnabled ? '🔊' : '🔇';
    if (!voiceEnabled && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      container.classList.remove('is-speaking');
    }
  });

  chips.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-q]');
    if (btn) handleUserQuery(btn.dataset.q);
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    handleUserQuery(input.value);
    input.value = '';
  });
})();

# PetCare

PetCare es una plataforma veterinaria con tres espacios conectados: el sitio público, el portal instalable para tutores y el panel de trabajo de la clínica. Está en español y funciona en escritorio y celular.

## Iniciar en Windows

Hacé doble clic en `Iniciar PetCare.bat`. El lanzador inicia el servidor local y abre el panel clínico.

- Sitio público: `http://127.0.0.1:8765/`
- App / portal de tutores: `http://127.0.0.1:8765/portal.html`
- Panel clínico: `http://127.0.0.1:8765/clinic.html`
- Estado del servidor: `http://127.0.0.1:8765/api/health`

También podés ejecutar `python server.py` desde esta carpeta. La primera ejecución crea `data/petcare.sqlite3` con pacientes, tutores e historiales ficticios.

## Instalar la app

El portal es una PWA: se puede agregar a la pantalla de inicio desde el navegador del celular y abrir como una app. En Chrome o Edge, usá “Instalar PetCare”; en iPhone o iPad, abrí el menú Compartir de Safari y elegí “Agregar a pantalla de inicio”. La app necesita HTTPS o `localhost` para instalarse; en una instalación remota también necesita que el backend esté disponible.

El service worker guarda los archivos de la interfaz para abrir la estructura básica sin conexión. Consultas, turnos y cambios requieren conexión con el servidor. El almacenamiento y la autenticación de la demo son locales.

## Cuenta de demostración del portal

- Correo: `carlos.ruiz@petcare.demo`
- Contraseña: `bienvenida2026`

También se puede crear una cuenta nueva. Si el teléfono coincide con uno registrado en una ficha de la clínica, esa ficha queda vinculada a la cuenta del tutor.

## Funciones

### Sitio público

- Presentación de PetCare con accesos directos al portal y al panel clínico.
- Diseño adaptable, navegación móvil, información de funciones y aviso visible para emergencias.

### App / portal de tutores

- Crear una cuenta vinculada al teléfono registrado en la clínica.
- Consultar las mascotas asociadas, los registros que la clínica comparte y las solicitudes de turnos.
- Registrar una mascota, pedir una consulta o teleconsulta y elegir entre horarios disponibles.
- Instalar en la pantalla de inicio y abrir en modo app.
- Las solicitudes quedan pendientes hasta que la clínica las confirme.
- La opción “Emergencia” genera una alerta prioritaria y recuerda acudir a la clínica o a una guardia, sin esperar un turno común.

### Panel clínico

- Directorio y registro de pacientes.
- Agenda con horarios libres, detección de superposiciones y duración por tipo de consulta.
- Duraciones iniciales: vacunación 15 min, control 20 min, consulta general 30 min, teleconsulta 25 min, estudio diagnóstico 45 min y procedimiento 60 min. El equipo puede ajustar la duración al crear cada turno.
- Emergencias marcadas como atención inmediata, fuera de la agenda habitual y visibles en el inbox prioritario.
- Inbox, recordatorios y borradores SOAP guardados localmente.

## Alcance y seguridad

Los datos incluidos son ficticios. El servidor solo escucha en `127.0.0.1`; las contraseñas se guardan con hash y las sesiones del portal usan cookie HTTPOnly. La base local no está cifrada y el panel clínico todavía no tiene usuarios ni permisos por rol. No cargues historias clínicas reales hasta agregar esos controles y desplegar el sistema en una infraestructura segura.

El sitio del repositorio no es, por sí solo, un despliegue público: PetCare necesita publicar también el backend Python y configurar HTTPS, almacenamiento persistente, respaldos, acceso por rol y monitoreo. WhatsApp, videollamadas, correo, calendarios y EHR/PMS todavía no están conectados. La teleconsulta se puede solicitar, pero el enlace de video necesita una integración posterior. El historial del tutor muestra únicamente registros marcados como compartidos por la clínica; los borradores SOAP no aparecen en esa vista.

## Archivos principales

- `index.html`, `landing.css`, `landing.js`: sitio público.
- `portal.html`, `portal.css`, `portal.js`: portal instalable para tutores.
- `manifest.webmanifest`, `service-worker.js`, `icons/`: instalación y caché de la app (iconos PNG para Android/iPhone y SVG).
- `clinic.html`, `styles.css`, `app.js`: panel clínico.
- `server.py`: API, sesiones, disponibilidad y persistencia SQLite.
- `Iniciar PetCare.bat`: lanzador para Windows.
- `data/petcare.sqlite3`: base local creada al iniciar el servidor; no se publica en Git.

# PetCare

PetCare es un prototipo local de gestión veterinaria con dos experiencias conectadas: el panel del equipo clínico y el portal de tutores. La interfaz está en español, se adapta a móvil y escritorio, y guarda datos en SQLite mediante una API Python sin dependencias externas.

## Iniciar en Windows

Hacé doble clic en `Iniciar PetCare.bat`. El lanzador reutiliza el servidor local si ya está abierto; si no, lo inicia y abre el panel de la clínica.

- Panel de la clínica: `http://127.0.0.1:8765/`
- Portal de tutores: `http://127.0.0.1:8765/portal.html`

También podés ejecutar `python server.py` desde esta carpeta. La primera ejecución crea `data/petcare.sqlite3` con pacientes, tutores e historiales ficticios.

## Cuenta de demostración del portal

- Correo: `carlos.ruiz@petcare.demo`
- Contraseña: `bienvenida2026`

También se puede crear una cuenta nueva. Si el teléfono coincide con uno registrado en una ficha de la clínica, esa ficha queda vinculada a la cuenta del tutor.

## Funciones

### Panel de la clínica

- Directorio y registro de pacientes.
- Agenda con horarios libres, detección de superposiciones y duración por tipo de consulta.
- Duraciones iniciales: vacunación 15 min, control 20 min, consulta general 30 min, teleconsulta 25 min, estudio diagnóstico 45 min y procedimiento 60 min. El equipo puede ajustar la duración al crear cada turno.
- Emergencias marcadas como atención inmediata, fuera de la agenda habitual y visibles en el inbox prioritario.
- Inbox, recordatorios y borradores SOAP guardados localmente.

### Portal de tutores

- Crear una cuenta vinculada al teléfono registrado en la clínica.
- Consultar las mascotas asociadas, los registros que la clínica comparte y las solicitudes de turnos.
- Registrar una mascota, pedir una consulta o teleconsulta y elegir entre horarios disponibles.
- Las solicitudes quedan pendientes hasta que la clínica las confirme.
- La opción “Emergencia” genera una alerta prioritaria y recuerda acudir a la clínica o a una guardia, sin esperar un turno común.

## Alcance y seguridad

Los datos incluidos son ficticios. El servidor solo escucha en `127.0.0.1`; las contraseñas se guardan con hash y las sesiones del portal usan cookie HTTPOnly. La base local no está cifrada y el panel clínico todavía no tiene usuarios ni permisos por rol. No cargues historias clínicas reales hasta agregar esos controles y desplegar el sistema en una infraestructura segura.

WhatsApp, videollamadas reales, correo, calendarios y EHR/PMS todavía no están conectados. La teleconsulta se puede solicitar, pero el enlace de video necesita una integración posterior. El historial del tutor muestra únicamente registros marcados como compartidos por la clínica; los borradores SOAP no aparecen en esa vista.

## Archivos

- `index.html`, `styles.css`, `app.js`: panel clínico.
- `portal.html`, `portal.css`, `portal.js`: portal de tutores.
- `server.py`: API, sesiones, disponibilidad y persistencia SQLite.
- `Iniciar PetCare.bat`: lanzador para Windows.
- `data/petcare.sqlite3`: base local creada al iniciar el servidor.

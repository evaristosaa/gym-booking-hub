# Gym Booking Hub

App independiente para que cada persona configure y consulte sus reservas semanales de gimnasio.

## Qué es hoy

- Web estática preparada para GitHub Pages.
- Agenda de reservas y hora de lanzamiento configurables por cada usuario.
- Los datos de la demo se guardan solamente en el navegador del usuario.
- La reserva real queda deliberadamente fuera del frontend: requerirá un agente local seguro.

## Por qué hay dos piezas

GitHub Pages no puede guardar credenciales de WodBuster, mantener una sesión ni ejecutar una tarea un viernes con el navegador cerrado. Por tanto:

1. **GitHub Pages**: interfaz pública, agenda, configuración y estado.
2. **Agente local**: servicio que cada usuario instala en su propio equipo y que custodia sus credenciales y ejecuta las reservas.

No se publicarán contraseñas, cookies ni tokens en este repositorio.

## Ejecutar la interfaz

Abre `public/index.html` en un navegador o publícala como GitHub Pages desde la carpeta `public`.

## Estado

La interfaz inicial es funcional como agenda local. La conexión con el agente local y WodBuster se implementará después de acordar el protocolo y la autenticación.


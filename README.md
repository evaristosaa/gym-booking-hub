# Gym Booking Hub

App independiente para que cada persona configure y consulte sus reservas semanales de gimnasio.

## Qué es hoy

- Web estática preparada para GitHub Pages.
- Agenda de reservas y hora de lanzamiento configurables por cada usuario.
- Los datos de la demo se guardan solamente en el navegador del usuario.
- La reserva real queda deliberadamente fuera del frontend: requerirá un backend seguro.

## Por qué hay dos piezas

GitHub Pages no puede guardar credenciales de WodBuster, mantener una sesión ni ejecutar una tarea un viernes con el navegador cerrado. Por tanto:

1. **GitHub Pages**: interfaz pública, agenda, configuración y estado.
2. **Backend seguro**: servicio que cifra credenciales, ejecuta las reservas y notifica el resultado al móvil.

No se publicarán contraseñas, cookies ni tokens en este repositorio.

## Ejecutar la interfaz

Abre `public/index.html` en un navegador o publícala como GitHub Pages desde la carpeta `public`.

## Estado

La interfaz inicial es funcional como agenda local. La conexión con el backend y WodBuster se implementará después de completar autenticación y la bóveda cifrada.

## Cloud

El proyecto Google/Firebase de desarrollo es `gym-booking-hub-20260913`:

- Firestore Native en `europe-west1`.
- Firebase web app configurada para la PWA.
- Presupuesto mensual de 5 EUR creado para ese proyecto.

No hay backend desplegado, proveedores de autenticación habilitados ni credenciales de usuarios almacenadas todavía.

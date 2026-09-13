# Arquitectura inicial

```text
GitHub Pages (público, estático)
  ├─ Agenda y configuración local
  ├─ Estado de conexión del agente
  └─ Sin contraseñas ni ejecución programada

Agente local de cada usuario (privado)
  ├─ Credenciales cifradas/locales del proveedor
  ├─ Planificador viernes 15:30
  ├─ Reserva y reconciliación manual
  └─ Resultado firmado/validado hacia la interfaz
```

El agente local no estará expuesto a Internet. La siguiente fase definirá un emparejamiento explícito y revocable entre interfaz y agente.


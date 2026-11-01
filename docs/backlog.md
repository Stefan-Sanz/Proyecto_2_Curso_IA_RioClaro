---
Backlog Proyecto Río Claro

# Backlog del proyecto Río Claro

## Historias de usuario

1. **Facturas:** como usuario, quiero cargar una factura PDF o imagen para
   extraer automáticamente sus datos.

2. **Revisión:** como usuario, quiero revisar los datos extraídos para validar
   que sean correctos.

3. **Asistente:** como cliente o empleado, quiero hacer preguntas mediante un
   chat para obtener respuestas basadas en documentación autorizada.

4. **Voz:** como usuario, quiero hacer consultas por voz para interactuar de
   manera más sencilla.

5. **IA responsable:** como evaluador, quiero documentación y evidencias de
   Responsible AI para comprender los controles y límites de la solución.

## Estado para la demostración

- Historias 1 y 2: flujo de análisis, revisión, confirmación y guardado local
  de demostración implementado y validado manualmente.
- Historia 3: asistentes de clientes y personal implementados con Foundry y
  contexto autorizado; verificados con la cuenta disponible.
- Historia 4: chat de voz de clientes y empleados implementado con Azure
  Speech F0 existente y confirmado manualmente por el usuario. No se persiste
  el audio de entrada.
- Historia 5: existe documentación de controles y límites en
  `responsible-ai.md`; no se realizó auditoría ni evaluación formal de impacto.

Los pedidos, catálogo e inventario son datos de demostración. La cuenta
administradora se verificó; las pruebas separadas de `obrero` y `finanzas` se
omitieron por decisión del usuario y no se reportan como roles validados. El
usuario confirmó que cerró sesión de Entra ID varias veces y tuvo que volver a
iniciar sesión para acceder a la información protegida.
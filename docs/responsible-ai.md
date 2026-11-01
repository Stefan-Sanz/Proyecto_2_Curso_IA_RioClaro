# IA responsable — demostración escolar Río Claro

Este documento describe controles y limitaciones de la demostración; no representa una auditoría ni una evaluación formal de impacto.

## Equidad

La aplicación utiliza los mismos servicios para los archivos que se cargan. No se ha realizado una evaluación de equidad con un conjunto representativo de facturas ni se puede concluir que el sistema esté libre de sesgo.

## Confiabilidad y seguridad

Azure AI Document Intelligence puede omitir o extraer incorrectamente campos. Una persona debe verificar el resultado antes de usarlo. Los estados y señales de duplicidad son demostrativos y no constituyen una validación contable. Las pruebas unitarias usan servicios simulados y no miden precisión del modelo.

## Privacidad y seguridad

Las credenciales se configuran fuera del código fuente. Para probar Document Intelligence deben usarse documentos sintéticos o autorizados, ya que el archivo se envía al servicio Azure configurado. Los datos de facturas solo se copian a SQLite local si el usuario lo solicita tras revisarlos; la base está excluida del repositorio y no debe recibir documentos no autorizados. El acceso genérico a pedidos no verifica identidad y solo se usa con datos sintéticos. Para voz, el audio se envía al recurso Azure Speech existente para su procesamiento; la aplicación no guarda el audio de entrada, pero el uso del servicio puede generar cargos.

## Inclusión

La carga de facturas acepta PDF, JPG, JPEG y PNG. Los asistentes de clientes y
personal también admiten entrada y respuesta por voz mediante Azure Speech.
Esto no equivale a una evaluación completa de accesibilidad ni de usabilidad
con personas con distintas necesidades.

## Transparencia

La pantalla muestra los campos reconocidos por Document Intelligence. El asistente utiliza archivos locales autorizados por audiencia/rol como contexto completo, sin recuperar fragmentos por relevancia. Puede mostrar nombres de archivos que el modelo cite y que la aplicación valida contra las fuentes enviadas; esto no garantiza que la referencia sea una cita literal ni que la respuesta sea correcta. El catálogo, inventario y pedidos son datos sintéticos. La interfaz advierte que la IA puede cometer errores y que el acceso genérico a pedidos no verifica identidad. El usuario confirmó el chat de voz en ambas experiencias; esta comprobación funcional no es una evaluación de precisión, privacidad más allá de la no persistencia del audio en la aplicación, ni accesibilidad.

## Responsabilidad

Las personas deben revisar los resultados y no tomar decisiones de negocio basadas únicamente en la salida del modelo. Solo proveedor, RFC de proveedor/cliente, cliente, folio, subtotal, total e IVA se evalúan para confianza; valores menores a 80% o sin confianza requieren confirmación humana antes de confirmarse como vigentes. La SQLite de demostración guarda campos bajo acción explícita, pero no es un registro de auditoría.

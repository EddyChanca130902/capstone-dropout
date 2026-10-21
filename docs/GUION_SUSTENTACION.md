# Guion de sustentación · EarlySign

**Criterio de evaluación:** 6. Exposición y sustentación técnica
**Duración de referencia:** 10-12 minutos de exposición + 5-8 de preguntas
**Uso:** ensayo cronometrado + preparación de respuestas.

---

## 1. Estructura de la exposición (12 minutos)

| Min | Bloque | Contenido | Qué se proyecta |
|---|---|---|---|
| 0:00-1:00 | **Contexto y problema** | UPN, orientación, detección tardía y dependiente del criterio individual. La necesidad: una señal comparable, trazable y explicable. | Diapositiva 1 |
| 1:00-2:30 | **Alternativas evaluadas** | Dataset (Perú vs Portugal vs propio UPN), modelo (LR/RF/XGB con métricas), backend, frontend, BBDD, k6, despliegue. Decisión y justificación. | Diapositiva 2 |
| 2:30-3:30 | **Arquitectura** | Tres capas, diagrama, por qué FastAPI + Supabase + Angular. Aislamiento por RLS. | Diapositiva 3 (diagrama) |
| 3:30-5:00 | **El modelo** | Dataset, target, métricas (AUC 0.934, recall 0.831), por qué XGBoost, umbrales, SHAP. Limitaciones: proxy, 23 variables imputadas, área poco informativa. | Diapositiva 4 + `reports/figures/06_shap_global_xgb.png` |
| 5:00-6:30 | **El defecto encontrado y su corrección** | 6 de 13 variables se descartaban en silencio. Causa, evidencia, corrección y test de regresión. **Es el momento fuerte de la exposición.** | Diapositiva 5 (código antes/después) |
| 6:30-8:00 | **Demo en vivo** | Login → panel → evaluar → resultado → historial → privacidad | La aplicación |
| 8:00-9:30 | **Calidad y rendimiento** | Pirámide de pruebas con cifras, k6 (371 req/s, p95 112 ms), optimizaciones (JWKS, ruta rápida, OMP). | Diapositiva 6 |
| 9:30-10:30 | **Seguridad y datos** | RLS, JWT local, argon2, secretos, CORS, política de privacidad. | Diapositiva 7 |
| 10:30-11:30 | **Evaluación y siguientes pasos** | Indicadores técnicos, operativos y de resultado; instrumentos listos; plan de validación con datos de la UPN. | Diapositiva 8 |
| 11:30-12:00 | **Cierre** | EarlySign convierte registros en una señal comparable, trazable y explicable, sin sustituir el criterio del orientador. | Diapositiva 9 |

**Regla de oro:** si el demo falla, la exposición no se cae. Todo lo anterior ya está medido y documentado; el demo es una confirmación, no la prueba.

---

## 2. Plan de contingencia del demo

| Fallo | Respuesta inmediata |
|---|---|
| La API está dormida (arranque en frío de ~20 s) | "Estamos viendo el arranque en frío del plan gratuito; en producción con plan pago desaparece." Medir el tiempo en voz alta: es un dato, no un accidente. |
| Falla la red | Continuar con las capturas de pantalla (`reports/Pruebas.md` y las capturas E2E) y explicar el recorrido |
| El login se rechaza | Tener a mano la credencial de prueba y el motivo (rate limit de Supabase → caché de 60 s ya implementada) |
| El evaluador pregunta por un error visto | Reconocerlo con precisión: qué es, dónde está documentado y qué mitigación tiene |

> **Antes de la sustentación:** abrir la aplicación y la API 5 minutos antes para que el plan gratuito no esté dormido.

---

## 3. Preguntas con respuesta preparada

### Sobre el problema y el alcance

**P. ¿Por qué un sistema de alerta temprana y no una hoja de cálculo con los datos de los estudiantes?**
Porque el problema no es la disponibilidad del dato, sino la falta de un criterio **cuantificable, comparable y trazable** para priorizar. La hoja de cálculo depende de quien la revise; el sistema aplica el mismo criterio a todos, deja registro de quién decidió qué y permite medir cuánto se ayuda (indicadores I-E1 a I-E8 del plan de evaluación).

**P. ¿Qué pasa si el orientador no está de acuerdo con la predicción?**
Puede corregir el nivel desde el historial. La corrección queda registrada con su marca de tiempo, y el sistema **no** restringe esa capacidad: el modelo es un apoyo, no una decisión. Además, el plan de evaluación mide el caso en el que la alerta no era útil (falsos positivos, I-E3), que es información para recalibrar.

**P. ¿No es este un sistema de decisión automatizada prohibida por la normativa?**
No. El sistema no decide: devuelve una estimación y el humano decide. Está declarado en la interfaz, en la política de privacidad y en el informe. El dato de entrada es anónimo en cuanto al modelo: los estudiantes no son identificables por el modelo.

### Sobre el modelo

**P. ¿Por qué Portugal y no datos peruanos?**
Porque el dataset peruano disponible (768 filas, 40+ ítems psicométricos) no es recolectable en un formulario de orientación y su modelo daba AUC 0.68 con solo 591 filas utilizables. Se evaluó, se implementó parcialmente y se documentó como alternativa descartada (§4.1 del informe). El dataset de la UPN es la fase siguiente y ya tiene el protocolo definido (§3.4 del plan de evaluación).

**P. ¿Qué tan fiable es un modelo entrenado en otro país?**
Es un proxy, y por eso el producto obliga a una lectura crítica: los umbrales son configurables, el panel muestra la probabilidad y no una categoría cerrada, y la evaluación real se mide con los instrumentos definidos (I-E1 e I-E2). El riesgo R1 del informe asume explícitamente esta limitación.

**P. ¿Por qué XGBoost y no regresión logística, que es más simple?**
Por recall: en alerta temprana interesa detectar más casos, aunque haya más falsos positivos. XGBoost da 0.831 de recall frente a 0.838 de la logística, con F1 superior (0.818 vs 0.814) y el doble de PRC. La diferencia de AUC es de 0.002. Es una decisión con criterio, y está planteada como trabajo futuro reevaluar si se priorizara interpretabilidad.

**P. ¿El área de estudios casi no influye en la predicción. No es un defecto?**
Lo es, y está documentado como tal. XGBoost no divide por `Nursing` ni `Management` (importancia 0) porque, en el dataset, esas carreras no separan el riesgo. El mapeo de las 5 áreas del formulario a 5 carreras portuguesas es una simplificación que el propio dato desmiente. Es un punto del informe y del trabajo futuro: con datos de la UPN el área debe recuperar peso.

**P. ¿Qué pasa con el 2.º semestre? ¿No es tarde para una alerta?**
Correcto, y por eso medí la ablación: sin el 2.º semestre el AUC baja de 0.936 a 0.914 y el recall de 0.761 a 0.690. Sigue siendo utilizable, así que la versión "realmente temprana" (solo 1.er semestre, 13 variables, AUC 0.907) es viable y está priorizada en el trabajo futuro. El sistema actual prioriza la cobertura y la simplicidad del formulario.

**P. ¿Cómo distingo un estudiante que se va aира de uno que solo tiene malas notas?**
Con varias señales a la vez: matrícula al día, deuda, Approved del 2.º semestre (la variable de mayor peso: 20.8 % de importancia), notas y edad. Un solo estudiante con mal rendimiento no dispara la alerta: el modelo exige el patrón. Por eso los 3 factores principales del SHAP son útiles de explicar.

**P. ¿Cómo se evita que una predicción incorrecta harms al estudiante?**
No hay decisión automática. La interfaz lo dice, el orientador puede corregir el nivel, y el registro de cada evaluación permite auditar qué se decidió y con qué información. Además, se miden los falsos positivos (I-E3) para ajustar los umbrales.

### Sobre la arquitectura

**P. ¿Por qué FastAPI y no Django?**
Django es excelente para aplicaciones con ORM, admin y formularios HTML; aquí el núcleo es una API que sirve una inferencia y expone un contrato tipado a un SPA. FastAPI da ese contrato con validación y OpenAPI automáticos, y comparte lenguaje con el modelo. Django habría añadido peso sin resolverlos.

**P. ¿Por qué Angular y no React?**
Angular aporta formularios reactivos con validación declarativa, guardas de ruta, interceptores con refresco de token y un builder optimizado, y su ecosistema de herramientas de formularios es más maduro. La decisión real fue de continuidad: el proyecto ya tenía un frontend y el criterio fue dejar Streamlit como cliente de referencia, no migrar a React y luego a otra cosa.

**P. ¿Por qué Supabase y no PostgreSQL en la UPN con Auth0?**
Supabase aporta Postgres + Auth + RLS en un servicio, con un panel que permite crear usuarios sin tocar código. El argumento decisivo no es el costo: es que **RLS aplica el aislamiento en la base de datos**, no en el código. Un error en la API no puede exponer datos de otro orientador. Con Auth0 habría que implementar ese aislamiento a mano, que es precisamente donde se suelen colar las fugas.

**P. ¿No es un punto débil depender de un solo proveedor?**
Sí, y está en el riesgo R6. La mitigación implementada: el healthcheck reporta el estado de Supabase y la inferencia del modelo sigue funcionando sin persistencia. Migrar a un PostgreSQL propio con el pooler de Supavisor es un cambio de repositorio, no de arquitectura: la capa de datos está aislada en `api/services/`.

**P. ¿Por qué no usaste el cliente de Supabase para Python?**
Porque la versión instalada (2.33.0) es incompatible consigo misma: su `ClientOptions` no expone el atributo `storage` que su propio cliente de autenticación requiere, y la creación del cliente falla con `AttributeError`. Como la aplicación solo necesita operaciones de tabla, uso PostgREST directamente, que además es más ligero y permite mantener conexiones persistentes (clave para el rendimiento).

**P. ¿Por qué el token se verifica en tu servidor y no en Supabase?**
Para no hacer una llamada de red a Supabase en cada petición. Con JWKS cacheado, la verificación es local y criptográfica (firma ES256, `kid`, `exp`, `iat`, `aud`, `sub`). Es un requisito para las pruebas de carga: sin esto, la latencia por request sería de ~300 ms solo en verificación.

**P. ¿Cómo sé que un token no fue manipulado?**
La firma se valida con la clave pública del servidor de Supabase, y se comprueban `exp`, `iat` (con margen de 300 s por desfase de reloj), `aud` y `sub`. Un token con `alg: none` o con firma inválida se rechaza con 401. Hay un test que lo verifica explícitamente.

**P. ¿Qué pasa si alguien entra en la base de datos?**
El servicio se expone con un usuario de solo lectura y sin la clave de servicio; la clave de servicio vive en el gestor de secretos del proveedor y nunca sale del servidor. Aun así, la seguridad no depende de ocultar claves: depende de que la política de RLS limite lo que cada token puede ver.

### Sobre calidad y rendimiento

**P. ¿Cómo sé que el sistema funciona y no solo que compila?**
Porque hay 72 pruebas automatizadas (59 de backend, 13 de frontend), un test de integración que hace login, crea, lista, corrige y borra contra Supabase real, un recorrido end-to-end con navegador real sobre la versión desplegada con captura de cada pantalla y 0 errores de consola, y cuatro escenarios de carga con k6 con umbrales de aceptación.

**P. ¿Cuál fue el error más importante que encontraste?**
Que 6 de las 13 variables del formulario no influían en la predicción. Se enviaban como `"1"/"0"` y códigos numéricos de carrera, mientras el encoder esperaba `"Male"/"Female"` y nombres; como el encoder ignora lo desconocido, las descartaba **sin error**. El modelo "funcionaba" y las pruebas también pasaban, porque nadie comprobó que las variables influyeran. La corrección fue el mapeo canónico, la imputación por medianas de las 23 variables no capturadas, y sobre todo un test de regresión que recorre los 12 campos y exige que cada uno mueva la probabilidad. Es la respuesta a por qué el plan de calidad insiste en verificar el comportamiento, no solo la ejecución.

**P. ¿Cómo llegaron a 0.34 ms por predicción?**
El perfilado mostró que el 90 % del tiempo estaba en el preprocesado de sklearn: validar un DataFrame de una sola fila cuesta ~5 ms. Como el transformador es lineal (escalado) más una búsqueda one-hot, lo reproduje de forma vectorizada, y **añadí un test que verifica que la ruta rápida da el mismo resultado que el pipeline original** (40 filas reales, tolerancia 1e-9). Antes de eso, además, se cacheó el JWKS (que añadía 300 ms por request) y se fijó `OMP_NUM_THREADS=1` para evitar la sobrecoste de hilos de XGBoost bajo concurrencia. Con 50 VUs, el p95 pasó de 646 ms a 10.5 ms.

**P. ¿371 req/s es mucho o poco?**
Para el caso de uso real es de sobra: una unidad de orientación con 10 orientadores haciendo 20 evaluaciones por hora no llega a 1 req/s. La cifra sirve para demostrar que el sistema no tiene un cuello de botella propio. En el plan gratuito de Render la cifra cae a 44 req/s con un 3 % de errores, y la causa es la infraestructura (0.5 GB, CPU compartida, 250 ms de red hasta Oregon), no el código: la inferencia en el servidor de producción sigue tardando 0.97 ms.

**P. ¿Qué se rompe primero si falla algo?**
La persistencia: si Supabase no responde, el healthcheck pasa a "degradado" y las inferencias siguen funcionando, pero no se guardan. Lo verifiqué de forma explícita. El plan de continuidad está en el plan de seguridad.

### Sobre datos y evaluación

**P. ¿Cómo saben que EarlySign es útil y no solo que funciona?**
Por eso existe el plan de evaluación: 9 indicadores técnicos ya medidos, 8 operativos que se extraen del sistema y 8 de resultado (detección temprana, aciertos, falsos positivos, ahorro de tiempo, utilidad, confianza, usabilidad SUS, claridad de la priorización), con instrumentos concretos: un cuestionario pre/post con escala Likert y SUS, una hoja de uso en SQL y una ficha de seguimiento de casos a 30-60 días. Cada afirmación se contrasta con dos fuentes independientes y hay criterios de decisión explícitos para cada resultado.

**P. ¿Cuándo sabrán si funciona en la UPN de verdad?**
Cuando haya datos propios. El protocolo ya está definido: extracción del padrón y de expedientes de 2-3 cohortes, reconstrucción del dataset, reentrenamiento con el mismo protocolo y comparación de métricas con el proxy. Si el modelo propio no supera al de Portugal, se mantiene el proxy con los umbrales recalibrados. La decisión se documenta en cualquiera de los dos casos.

**P. ¿Qué pasa con los datos de los estudiantes al final?**
La política de privacidad fija la conservación durante el seguimiento académico y por el plazo que fije la institución. El sistema no hace copias de seguridad propias: eso es responsabilidad de la UPN a través del proveedor. Los derechos (acceso, rectificación, supresión, oposición) se ejercen ante la institución, que puede identificar la evaluación a partir del DNI registrado.

### Sobre el proceso

**P. ¿Qué fue lo más difícil?**
Entender que el problema del modelo no era el modelo sino el contrato entre el formulario y el preprocesado. Un modelo con AUC 0.934 que recibe variables mal codificadas produce predicciones incorrectas con toda la apariencia de estar bien. Lo que aprendí: en un sistema predictivo hay que probar el comportamiento, no solo la ejecución.

**P. ¿Qué haría distinto si volviera a empezar?**
Validar el contrato de datos **antes** de construir la interfaz. Si hubiera empezado por el test que exige que cada campo mueva la probabilidad, habría detectado el defecto en la primera semana y no en la fase de migración. También reservaría tiempo para el plan de evaluación desde el inicio, porque es lo que convierte un proyecto técnico en un proyecto con valor institucional.

**P. ¿Qué queda pendiente?**
Seis acciones concretas: migrar Supabase a la región de la UPN, contratar el plan de hosting, añadir la clave `anon` real, rotar las claves si el `.env` se compartió, calibrar los umbrales con la capacidad real y publicar la variante de alerta temprana sin el 2.º semestre. Están todas en el §7 del README y en el §13 del informe.

---

## 4. Frases de transición útiles

- "Antes de mostrar el resultado, quiero explicar el defecto que encontramos, porque explica por qué el resto del diseño es como es."
- "Esta cifra es del dataset de entrenamiento, no de la UPN; por eso el plan de evaluación define cómo medir el desempeño real."
- "El aislamiento no está en el código, está en la base de datos; esa es la diferencia entre un control y una convención."
- "El sistema no decide: informa. Esa distinción es la base de su aceptación ética y legal."

---

## 5. Checklist antes de la sustentación

- [ ] API despertada 5 minutos antes (evita el arranque en frío de 20 s)
- [ ] `CORS_ORIGINS` actualizado en Render con el dominio exacto del frontend
- [ ] Credenciales de prueba cambiadas y anotadas
- [ ] Datos de prueba limpiados en Supabase (dejar solo los casos reales)
- [ ] Diapositivas 1-9 listas (una por bloque del guion)
- [ ] `reports/figures/` y `docs/` abiertos y listos para mostrar
- [ ] Ensayo cronometrado (12 min) con el cronómetro visible
- [ ] Segunda persona revisa ortografía de las diapositivas

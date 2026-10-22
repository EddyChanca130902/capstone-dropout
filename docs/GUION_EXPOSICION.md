# Guión de exposición · EarlySign (texto hablado)

**Criterio 6 · Exposición y sustentación técnica** · UPN · EarlySign · 21 de octubre de 2026
**Duración:** 12-13 minutos + 5-8 de preguntas
**Uso:** ensaya en voz alta con cronómetro. El texto marcado como *hablado* es literal: dilo así o con tus palabras, pero conserva los **datos concretos** (cifras, nombres de tablas, rutas), que son lo que el jurado recuerda.

> **Regla de oro:** si el demo falla, la exposición no se cae. Todo lo que vas a decir está medido y documentado. El demo es una confirmación, no la prueba.

---

## Mapa de la exposición

| # | Parte | Min | Objetivo de la parte | Diapositiva |
|---|---|---|---|---|
| 0 | Apertura | 0:00 | Que el jurado sepa en 20 segundos qué es esto | 1 |
| 1 | El problema | 0:20 | Por qué existe el sistema | 1-2 |
| 2 | Decisiones y alternativas | 1:30 | Que sepas *elegir*, no solo usar | 3 |
| 3 | Arquitectura | 2:30 | Cómo está construido | 4 |
| 4 | El modelo | 3:30 | Qué predice y con quéExactitud | 5 |
| 5 | **El defecto encontrado** | 4:45 | **El momento fuerte: pensar como ingeniero** | 6 |
| 6 | Demo | 6:00 | Que lo vean funcionando | — |
| 7 | Calidad y rendimiento | 7:30 | Que está verificado, no supuesto | 7 |
| 8 | Seguridad y datos | 8:45 | Que es responsable con datos de estudiantes | 8 |
| 9 | Evaluación y siguientes pasos | 9:30 | Que sabes medir su valor | 9 |
| 10 | Cierre | 10:45 | Que quede una frase memorable | 10 |

---

## 0 · Apertura (0:00 - 0:20)

**[DIAPOSITIVA 1: título EarlySign + nombre + UPN]**

> *Buenos días. Mi nombre es ⟨nombre⟩ y presento **EarlySign**, un sistema de señales tempranas de abandono académico para la Universidad Privada del Norte.*
>
> *EarlySign es una herramienta de apoyo a la unidad de orientación: el orientador registra los datos del estudiante y el sistema devuelve una **probabilidad de abandono** y un nivel de riesgo, que permite decidir a quién acompañar primero.*
>
> *La frase que resume todo el proyecto es esta: **la plataforma informa, la persona decide.** No hay ninguna decisión automatizada sobre ningún estudiante.*
>
> *En los próximos doce minutos voy a mostrarles el problema, las decisiones técnicas que tomé, una arquitectura de tres capas, el modelo, un defecto real que encontré en mi propio código, la demostración funcionando y las pruebas que respaldan cada afirmación.*

*\[Pausa de 2 segundos. Cambia a la diapositiva 2.\]*

---

## 1 · El problema (0:20 - 1:30)

**[DIAPOSITIVA 2: el flujo actual vs. el flujo con EarlySign]**

> *La unidad de orientación trabaja con una limitación estructural: la detección de estudiantes en riesgo depende del criterio individual de cada orientador.*
>
> *Eso tiene tres consecuencias. La primera es que **la detección es tardía**: el estudiante llega a orientación cuando ya solicita ayuda, y no existe un mecanismo que revise de forma periódica a toda la población. La segunda es que **la priorización no es reproducible**: dos orientadores pueden ordenar la cola de trabajo de forma distinta ante el mismo expediente. Y la tercera es que **no queda registro** de por qué se priorizó a un estudiante y no a otro.*
>
> *¿Qué se necesita, entonces? Algo que convierta los datos que ya se registran en las tutorías en una **señal comparable, trazable y explicable**, y que ordene la cola de trabajo con un criterio cuantificable. Y aquí viene lo importante: **eso no significa automatizar la decisión**. Significa apoyar el criterio profesional con información que hoy no está disponible.*
>
> *EarlySign cubre ese hueco. El orientador registra 13 variables —identificación, situación socioeconómica y rendimiento de los dos semestres—, y el sistema responde en menos de un milisegundo.*

*\[Si vas con prisas: resume la parte de "tres consecuencias" en una sola frase y sigue.\]*

---

## 2 · Decisiones y alternativas (1:30 - 2:30)

**[DIAPOSITIVA 3: tabla de alternativas con la decisión marcada]**

> *Quiero detenerme en las decisiones, porque creo que es lo que diferencia un proyecto de un ejercicio.*
>
> *La primera decisión fue **de dónde salen los datos para entrenar el modelo**. Evalué tres opciones. La primera era un dataset peruano de intenciones de deserción: lo descargué, lo limpié y entrené un modelo con él. Funcionaba técnicamente, pero tenía solo 591 filas utilizables de 768, con 40 y tantos ítems psicométricos que un formulario de orientación jamás va a poder recoger, y su **AUC fue de 0,68**. Lo descarté y dejé documentada la evidencia. La segunda opción eran datos propios de la UPN, que es la correcta en el largo plazo, pero requiere dos o tres cohortes y no es viable en el plazo del proyecto. La tercera, y la que implementé, es el **dataset público de la Universidad de Minho**, con 4 424 registros y 37 variables. Con ese dataset el modelo alcanza **0,934 de AUC**.*
>
> *La segunda decisión fue el **algoritmo**. Comparé los tres candidatos con la misma partición estratificada: regresión logística con 0,932 de AUC, random forest con 0,934, y XGBoost con 0,934. Si me quedo con el AUC, elijo cualquiera. Pero en alerta temprana lo que importa es **detectar más casos**, es decir, el *recall*. XGBoost da 0,831 frente a 0,792 de random forest, y 0,818 de F1 frente a 0,811. Por eso elegí XGBoost: no el número más alto, sino el que detecta más abandonos.*
>
> *Y la tercera decisión fue la **arquitectura**, que es lo que más discutimos: pasé de un prototipo en Streamlit con SQLite a una aplicación de tres capas. ¿Por qué? Porque el prototipo no tenía autenticación, ni aislamiento entre orientadores, ni pruebas, ni trazabilidad. Eso no es un detalle de un trabajo de tesis: es lo que hace que un sistema pueda usarse en una institución.*

*\[No leas la tabla entera. Señala las tres filas y detente en el "por qué".\]*

---

## 3 · Arquitectura (2:30 - 3:30)

**[DIAPOSITIVA 4: diagrama de 3 capas]**

> *Esta es la arquitectura. Son tres capas y una regla: **la lógica del modelo nunca sale del servidor**.*
>
> *Arriba, **Angular 22**: una SPA con login, panel, formulario de evaluación, historial y la política de privacidad. Usa formularios reactivos con validación, un guard de rutas y un interceptor que refresca el token solo cuando hace falta.*
>
> *En medio, **FastAPI**: valida los contratos con Pydantic, carga el modelo una sola vez en memoria, y se comunica con la base de datos a través de una capa fina de repositorio.*
>
> *Abajo, **Supabase**: PostgreSQL con autenticación y, lo más importante, **Row Level Security**. Las políticas de seguridad están escritas **en la base de datos**, no en el código: cada fila lleva su `user_id` y la base de datos solo deja ver al orientador lo que es suyo. Eso significa que aunque hubiera un error en mi API, **no podría exponer datos de otro orientador**. Un filtro en el código se puede olvidar; una política de base de datos no.*
>
> *Cada evaluación guarda además **el snapshot de las entradas y la versión del modelo** que la produjo. Eso es lo que hace auditable una decisión: dentro de seis meses se puede reconstruir exactamente con qué datos y con qué modelo se_priorizó a un estudiante.*

---

## 4 · El modelo (3:30 - 4:45)

**[DIAPOSITIVA 5: métricas + figura SHAP global]**

> *El modelo es un XGBoost con 300 árboles, profundidad 4 y learning rate 0,05, entrenado sobre las 4 424 filas del dataset de Minho con el target binario "abandona / no abandona" — un 32 % de casos positivos.*
>
> *Las métricas del test split, que es un 20 % estratificado con semilla fija: **AUC 0,934**, recall 0,831 sobre la clase de abandono, precisión 0,806, F1 0,818 y un Brier de 0,092. La calibración es razonable: la probabilidad media que predice el modelo es 0,385 y la prevalencia real es 0,321.*
>
> *Y esta figura es la que más me importa, porque convierte el modelo en algo explicable: es el **SHAP global**, con la importancia de cada variable. Las dos variables que más pesan son **las asignaturas aprobadas del segundo semestre** y **el estado de la matrícula**; aparecen de nuevo la deuda y la beca. Ese perfil es el que le sirve al orientador: no un número, sino un motivo.*
>
> *Ahora, las limitaciones, porque son importantes y quiero ser explícito. **El modelo es un proxy de Portugal**: está entrenado con datos de otro país y no tengo evidencia de que rinda igual en la UPN. **El formulario recoge 13 de las 36 variables** del modelo; las otras 23 se imputan con la mediana del entrenamiento. Y el **campo "área de estudios" casi no aporta**: el árbol no llega a dividir por dos de las cinco áreas porque en el dataset esas carreras no separan el riesgo.*

---

## 5 · El defecto encontrado (4:45 - 6:00) ⭐ PARTE CENTRAL

**[DIAPOSITIVA 6: código antes / después + el test de regresión]**

> *Quiero detenerme aquí, porque es la parte de la que más aprendí y creo que es la que mejor explica el resto del diseño.*
>
> *Cuando terminé la primera versión del predictor, todo funcionaba: la interfaz andaba, las pruebas pasaban, el modelo devolvía probabilidades. Pero al hacer una revisión de los datos que realmente llegaban al modelo, encontré que **seis de las trece variables del formulario no influían en el resultado**. Ni un error, ni un warning: el sistema simplemente las ignoraba.*
>
> *La causa era esta. El modelo fue entrenado con variables categóricas en texto: "Male", "Female", "Yes", "No", y nombres de carrera. Pero mi formulario enviaba **"1" y "0"**, y códigos numéricos de carrera. El codificador que usa el pipeline, cuando no reconoce un valor, no falla: lo descarta, porque está configurado para tolerar carreras que no vio en el entrenamiento. Así que el género, la beca, la deuda, el estado de la matrícula, la condición de desplazado y el área de estudio se estaban perdiendo en silencio.*
>
> *La corrección fue de dos partes. La primera, en el código: mapear a las etiquetas exactas que el modelo espera. La segunda, más importante, y esta es la que quiero deflation: **escribir el test que faltaba**. Hoy tengo un test que recorre los doce campos del formulario y **exige que cada uno mueva la probabilidad**. Ese test es la razón por la que el defecto no puede volver. No es un test de que "el código no se rompe": es un test de que **el comportamiento es el correcto**.*
>
> *La lección que me llevo es esta: **en un sistema predictivo hay que probar el comportamiento, no solo la ejecución**. Un modelo con 0,934 de AUC al que le entregas variables mal codificadas te da predicciones incorrectas con toda la apariencia de estar funcionando bien. Y de hecho, el MAE contra la predicción "correcta" bajó de 0,087 a 0,076 solo con corregir la codificación y la imputación, y la inferencia pasó de 10,7 milisegundos a 0,34 con una ruta de preprocesado que verifiqué contra el pipeline original con una tolerancia de 1 por 10 elevado.*

*\[Este es tu momento fuerte. Dilo despacio, mirando al jurado. Si alguien pregunta, tienes la respuesta en GUION_SUSTENTACION §3.\]*

---

## 6 · Demostración (6:00 - 7:30)

**[NAVEGADOR: https://capstone-dropout.vercel.app · dejar la sesión iniciada]**

> *Ahora les muestro el sistema funcionando. Empiezo en la pantalla de acceso.*

**[Clic: "Ingresar" con las credenciales de prueba]**

> *El acceso es por correo y contraseña contra Supabase Auth, y el token se valida en el servidor con la firma criptográfica y la clave pública del propio Supabase. No hay sesiones locales sin firmar.*

**[Clic: "Panel principal"]**

> *Este es el tablero. Arriba, los cuatro indicadores: estudiantes evaluados, evaluaciones realizadas, en riesgo alto y probabilidad promedio. En el centro, la distribución del riesgo por nivel y el riesgo por área. Abajo, las evaluaciones recientes. Y fíjense en esta nota al pie: **los niveles son una estimación del modelo para apoyar la revisión del orientador, no casos confirmados de abandono**. Eso es deliberado.*

**[Clic: "Evaluar estudiante"]**

> *El formulario es de dos pasos. Primero identificación y situación socioeconómica; después el rendimiento de los dos semestres, con validación en línea: no se pueden aprobar más asignaturas de las matriculadas.*

**[Rellenar y pulsar "Calcular riesgo y guardar"]**

> *La respuesta llega en milisegundos. En el servidor, la inferencia del modelo tarda 0,97 milisegundos: el resto es red.*

**[Clic: "Historial"]**

> *Y aquí queda registrado todo: fecha, estudiante, área, probabilidad, nivel. Se puede filtrar por área y por nivel, y se puede corregir el nivel manualmente —con la acción registrada—, porque el orientador tiene la última palabra.*

**[Clic en "Política de privacidad" en la barra lateral]**

> *Y esta es la política de privacidad, pública, sin necesidad de entrar. Detalla qué datos se registran, para qué, dónde se almacenan, cuánto tiempo se conservan y, sobre todo, **que el modelo se entrenó con datos de la UCI y que ninguno de los datos que ustedes introducen entra en ese entrenamiento**.*

---

## 7 · Calidad y rendimiento (7:30 - 8:45)

**[DIAPOSITIVA 7: pirámide de pruebas con cifras]**

> *Sobre calidad: el proyecto tiene **72 pruebas automatizadas** —59 de backend con pytest y 13 de frontend con Vitest—, un test de integración que hace login, crea, lista, corrige y borra contra Supabase real, un recorrido end-to-end con navegador real contra **esta misma versión desplegada**, con captura de cada pantalla y cero errores de consola.*
>
> *Y cuatro escenarios de carga con k6. En local, con 200 usuarios virtuales: **371 peticiones por segundo, p95 de 112 milisegundos y cero errores**, en 15 934 peticiones. En el despliegue real, con el plan gratuito de Render, la cifra baja a 44 por segundo: la causa es la infraestructura —memoria de 0,5 gigabytes, CPU compartida y 250 milisegundos de red hasta Oregon—, no el código, porque la inferencia en ese mismo servidor sigue tardando 0,97 milisegundos.*
>
> *Y las correcciones de rendimiento que sí fueron mías:.cachear las claves públicas de Supabase, que añadía 300 milisegundos a cada petición; fijar un solo hilo de OpenMP para XGBoost, que evitaba la sobrecoste de hilos bajo concurrencia; y la ruta rápida de preprocesado que mencioné antes. Con 50 usuarios virtuales, el p95 pasó de 646 a 10,5 milisegundos.*

> *Aquí tengo **cuatro figuras** que explican esto mejor que cualquier cifra suelta.* [Muestra `reports/figures/08_carga_tiempo.png`]
>
> *Esta primera es el comportamiento bajo carga en local: el caudal sube de forma prácticamente lineal con los usuarios virtuales, hasta un pico de 663 peticiones por segundo, y la latencia p95 se mantiene en el orden de cientos de milisegundos. No hay colapso.*
>
> *[Muestra `reports/figures/09_pruebas_cobertura.png`]*
>
> *Y esta es la cobertura: cinco niveles de prueba —unitarias, integración contra Supabase real, end-to-end con navegador real y carga— y cobertura en todos los módulos de negocio.*
>
> *[Muestra `reports/figures/10_comparativa_entornos.png`]*
>
> *Y aquí está la comparación entre local y producción.*
>
> *[Muestra `reports/figures/11_carga_comparada.png`]*
>
> *Esta es la figura que más me importa, porque resume el proyecto entero: **en local el caudal sigue subiendo; en producción se aplana**, porque la instancia compartida de 0,5 gigabytes del plan gratuito se satura. Pero fíjense en el dato que hay que mirar: **la inferencia del modelo en el servidor de producción tarda 0,97 milisegundos**. Si el código fuera el cuello de botella, ese número sería alto. Es bajo. Lo que tarda es la red.*
>
> *Por eso la recomendación del informe es un plan con recursos garantizados, y por eso el sistema está preparado para escalar: el modelo se carga una vez en memoria, no en cada petición.*

---

## 8 · Seguridad y datos (8:45 - 9:30)

**[DIAPOSITIVA 8: matriz de controles]**

> *En seguridad, el principio que guió todo fue: **no confiar en el código para proteger datos, sino en la base de datos**. Por eso el aislamiento es por políticas de RLS y no por un `where` en la consulta.*
>
> *El resto: los tokens se validan localmente con firma criptográfica, con margen para el desfase de reloj; las contraseñas se guardan con hash argon2; la clave de servicio de Supabase solo existe en el servidor; el CORS es explícito; las dependencias van pinneadas porque un modelo entrenado no es portable entre versiones; y el despliegue va en una imagen mínima de Docker.*
>
> *Hay dos cosas que quiero decir con honestidad. La primera: **el plan gratuito se duerme**, y la primera petición tras 15 minutos tarda 20 segundos. Es la razón principal por la que recomiendo un plan de pago para uso real. La segunda: todo esto está documentado en un plan de seguridad con la matriz de controles, y hay un script que verifica automáticamente el aislamiento creando dos usuarios reales y comprobando que cada uno solo ve lo suyo.*

---

## 9 · Evaluación y siguientes pasos (9:30 - 10:45)

**[DIAPOSITIVA 9: los 3 bloques de indicadores]**

> *Un sistema que funciona no es necesariamente un sistema que resuelve el problema. Por eso definí **cómo se va a medir si EarlySign sirve**.*
>
> *Y lo organizo así: **cada afirmación que sostiene este software tiene un KPI detrás**. No presento cifras sueltas; presento evidencia de lo que afirmo.*
>
> *Cuando digo «la estimación es fiable», lo sostengo con un AUC de 0,934 y un recall de 0,831 sobre un test del 20 % que el modelo nunca vió. Cuando digo «la plataforma aguanta la carga de la institución», lo sostengo con 371 peticiones por segundo con 200 usuarios virtuales y cero errores. Cuando digo «es seguro con datos de estudiantes», lo sostengo con el indicador de accesos a datos ajenos, que es cero, y verificado creando dos usuarios reales y comprobando que cada uno solo ve lo suyo. Y cuando digo «cada decisión es auditable», lo sostengo con que el cien por ciento de las evaluaciones guardan las entradas, la versión del modelo, el autor y las marcas de tiempo.*
>
> *Y el bloque que de verdad responde al problema son los **cuatro KPI de impacto**, que se calculan automáticamente desde el sistema: la **tasa de cobertura de intervención** (de cada estudiante detectado en alto riesgo, cuántos reciben acompañamiento), la **tasa de variación del nivel de riesgo** (cuántos bajaron de nivel tras la intervención), el **índice de resolución de variables modificables** (de las variables que el modelo marcó en alerta, cuántas mejoraron) y el **tiempo de respuesta** (cuántos días desde la detección hasta el inicio de la acción).*
>
> *Estos cuatro no los calculo yo a mano: los obtiene la API en `GET /api/v1/kpis/impacto` a partir de las evaluaciones y del registro de derivaciones. Para que tengan datos hacen falta dos cosas del orientador: evaluar y registrar la derivación.*
>
> *Y hay tres bloques de indicadores: los **técnicos**, que ya están medidos —AUC, recall, latencia, throughput—; los **operativos**, que se extraen del propio sistema —cobertura, tasa de reevaluación, tiempo de registro, distribución por nivel y trazabilidad—; y los **de resultado**, que son los que de verdad importan y que aún no puedo afirmar porque dependen del piloto: **cuántos estudiantes se detectan antes de que pidan ayuda** —mi objetivo es al menos el 50 %—, cuántos aciertos y cuántos falsos positivos produce la alerta, el tiempo ahorrado, la utilidad y la confianza percibidas por el orientador, y la usabilidad medida con la escala SUS.*
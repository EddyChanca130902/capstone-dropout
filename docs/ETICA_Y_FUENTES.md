# Ética, fuentes y uso de inteligencia artificial · EarlySign

**Criterio de evaluación:** 7. Ética y atención de observaciones
**Versión:** 1.0 · 21 de octubre de 2026 · UPN

---

## 1. Compromiso ético

EarlySign se desarrolla bajo los siguientes compromisos, asumidos de forma explícita por el equipo autor:

### 1.1 Respecto a la dignidad y la autonomía del estudiante

1. **El sistema no decide.** EarlySign estima una probabilidad; la decisión de acompañar, intervenir o escalar a la unidad correspondiente la toma siempre una persona, con su criterio profesional y su responsabilidad. La interfaz lo declara de forma visible (nota bajo el panel) y la política de privacidad lo recoge.
2. **No se realizan decisiones automatizadas con efectos jurídicos.** No hay sanciones, exoneraciones, exclusión de beneficios ni cambios de matrícula derivados del resultado.
3. **No se realiza perfilado con fines distintos del acompañamiento académico.** El dato se usa para priorizar atención, nada más.

### 1.2 Respecto a la privacidad y la protección de los datos

4. **Minimización**: solo se registran los 13 datos que el formulario necesita para la estimación. No se almacenan contactos, historiales académicos detallados ni datos de terceros.
5. **Aislamiento**: el acceso de cada orientador está limitado a sus propias evaluaciones, y la restricción está impuesta **por la base de datos** (RLS), no por el código de la aplicación: un error de programación no puede exponer datos ajenos.
6. **Trazabilidad**: cada evaluación conserva quién la hizo, cuándo, con qué modelo y con qué datos de entrada, lo que permite auditar cualquier decisión.
7. **Transparencia**: la política de privacidad es pública, está enlazada en el acceso al sistema y describe con precisión qué se recoge, para qué, quién lo ve y cuánto tiempo se conserva.
8. **No hay cesión a terceros con fines comerciales.** Los subencargados técnicos (hosting) tratan los datos exclusivamente por cuenta de la institución.

### 1.3 Respecto a la honestidad técnica

9. **El modelo es un proxy, y se dice.** Está entrenado con datos de Portugal, no de la UPN. La interfaz, la documentación y la política lo declaran; el informe enumera sus limitaciones (área poco informativa, 23 variables imputadas, banda MEDIA estrecha).
10. **No se presentan métricas de otro contexto como si fueran locales.** El AUC de 0.934 corresponde al dataset de entrenamiento; el desempeño real en la UPN se medirá con los instrumentos de [evaluación](EVALUACION_SOLUCION.md).
11. **Se documentan los defectos encontrados**, incluidos los que invalidaron resultados anteriores (el caso de las variables descartadas en silencio).

### 1.4 Respecto a las personas usuarias

12. **Accesibilidad**: la interfaz es responsive y navegable por teclado, con foco visible, contraste adecuado y textos alternativos.
13. **No se exige conocimiento técnico** para usarla: el formulario tiene dos pasos, validaciones en línea y mensajes de error en lenguaje claro.
14. **La sesión se puede cerrar** en un clic y el token se elimina del navegador.

---

## 2. Fuentes utilizadas

### 2.1 Datos

| Fuente | Uso | Licencia / atribución |
|---|---|---|
| UCI Machine Learning Repository — *Predict Students' Dropout and Academic Success* (Universidade de Minho) | Conjunto de entrenamiento y evaluación del modelo | Acceso abierto, uso académico. Citado en el informe, en la política de privacidad y en los notebooks |
| Dataset *Dropout intentions* (descartado) | Línea de investigación explorada y descartada | Abierto; se conserva únicamente como evidencia de la alternativa evaluada |

### 2.2 Documentación técnica

| Fuente | Uso |
|---|---|
| Documentación oficial de scikit-learn | `ColumnTransformer`, `StandardScaler`, `OneHotEncoder` y `Pipeline` |
| Documentación oficial de XGBoost | Parámetros del clasificador y `TreeExplainer` |
| Documentación de SHAP | Figuras de interpretabilidad global y local |
| Documentación de FastAPI, Pydantic, pydantic-settings | Endpoints, validación y configuración |
| Documentación de Angular | Componentes standalone, signals, rutas, guardas e interceptores |
| Documentación de Supabase | Auth, PostgREST, Row Level Security y trigger de `auth.users` |
| Documentación de k6 | Escenarios, métricas y umbrales |
| Documentación de PostgreSQL | Políticas de seguridad a nivel de fila |
| OWASP Top 10 y ASVS v4.0 | Marco de referencia para el plan de seguridad |
| Artículo de Brooke (1986) | Escala SUS para el instrumento de usabilidad |

### 2.3 Bibliografía académica citada

Se detailed en el §14 del [informe](../INFORME.md): Chen & Guestrin (2016), Harris et al. (2020), McKinney (2010), Pedregosa et al. (2011), Lundberg & Lee (2017).

---

## 3. Declaración de uso de inteligencia artificial

Durante el desarrollo de EarlySign se utilizó una herramienta de inteligencia artificial (asistente de programación conversacional) como **apoyo al desarrollo de software**. Esta declaración se formula de forma explícita y completa:

### 3.1 Usos realizados

| Uso | Descripción | Verificación |
|---|---|---|
| Revisión de código | Detección de problemas de corrección, de rendimiento y de estilo en el código propio | Cada corrección tiene un test de regresión asociado |
| Generación de pruebas | Redacción de los casos de prueba (unitarios, de integración y E2E) sobre el código ya implementado | Los tests son legibles y verificables por un tercero |
| depuración | Análisis de errores en ejecución (peticiones fallidas, incompatibilidad de dependencias, desfase de reloj) | La causa raíz se identificó y se documentó en el registro de incidencias |
| Documentación | Estructuración de README, planes e informes a partir de la evidencia del repositorio | Cada afirmación es verificable en el código o en las mediciones |
| Optimización | Propuestas de mejora de rendimiento (caché del JWKS, ruta rápida de preprocesado) | Cada optimización se midió antes y después |

### 3.2 Lo que **no** se delegó en la herramienta

- **El modelo predictivo**: la selección del dataset, la definición del target, la decisión de qué variables se capturan y la interpretación de las métricas son decisiones del autor, documentadas en el informe y en los notebooks.
- **La arquitectura y las restricciones**: FastAPI + Supabase + Angular y el mapeo de las 5 áreas de estudio fueron decisiones del autor.
- **El diseño de la base de datos y de las políticas de RLS**.
- **La validación de los resultados**: ninguna afirmación del informe se acepta sin verificación ejecutable.

### 3.3 Verificación y responsabilidad

Todo el código generado o sugerido por la herramienta fue **revisado, ejecutado y medido** antes de aceptarse. La responsabilidad del software, de sus resultados y de su documentación es del autor. Ningún fragmento se ha incorporado sin comprobación: el proyecto incluye 84 pruebas automatizadas, un recorrido end-to-end con navegador real y un registro de 17 incidencias detectadas y corregidas, que es la evidencia de ese proceso de verificación.

---

## 4. Atención de observaciones de la etapa T1

La evaluación de **T1** no dejó observaciones formales registradas. Aun así, entre ambas etapas se produjo una revisión de fondo que transformó el proyecto, y es verificable en el historial de commits:

| # | Revisión detectada en T1 | Cambio aplicado en T2 | Evidencia |
|---|---|---|---|
| 1 | El prototipo era un script de Streamlit con persistencia local en SQLite, sin autenticar | Arquitectura de tres capas con FastAPI, Supabase y Angular, con autenticación y aislamiento por usuario | `api/`, `frontend/`, `supabase/migrations/` |
| 2 | El predictor enviaba las variables categóricas con códigos en vez de etiquetas, y **6 de 13 variables no influían** en el resultado sin producir ningún error | Corrección del contrato formulario↔modelo, imputación por medianas del entrenamiento y test de regresión que lo blinda | `src/predictor.py`, `tests/test_predictor.py` |
| 3 | No existía ninguna prueba automatizada | 84 pruebas unitarias, integración contra Supabase real, recorrido E2E en producción y 4 escenarios de carga con k6 | `tests/`, `frontend/src/**/*.spec.ts`, `k6/`, `.github/workflows/ci.yml` |
| 4 | El modelo y su preprocesado se guardaban sin perfil de imputación: el resultado dependía de valores hardcodeados | `models/defaults.json` generado por script reproducible desde el dataset | `scripts/build_defaults.py` |
| 5 | No había control de acceso ni trazabilidad de las evaluaciones | RLS en la base de datos, `user_id`, `modelo_version` y `entradas` en cada fila | `supabase/migrations/0001_init.sql` |
| 6 | Sin documentación de despliegue ni continuidad operativa | Dockerfile, blueprint de Render, configuración de Vercel, guía de despliegue e informe de pruebas | `Dockerfile`, `render.yaml`, `frontend/vercel.json`, `DEPLOY.md`, `reports/Pruebas.md` |
| 7 | La interfaz era funcional pero no profesional | Rediseño completo: política de privacidad, empty states, loading states, hover states, iconos SVG y sistema de diseño | `frontend/src/app/` |

**Pendientes identificados y asumidos** (declarados en el §13 del informe): migrar el proyecto de Supabase a la región de la UPN, contratar un plan de hosting con recursos garantizados, calibrar los umbrales con la capacidad real de atención y validar el modelo con datos propios de la institución.

---

## 5. Resumen del compromiso

| Compromiso | Cómo se cumple | Dónde se verifica |
|---|---|---|
| No automatizar decisiones | La interfaz declara que es una estimación | `dashboard.html` (nota), `privacidad.html` |
| Minimizar datos | 13 variables; nada más se registra | `api/schemas/estudiante.py` |
| Aislar datos por usuario | RLS en la base de datos | `scripts/verify_supabase.py` |
| Ser transparente | Política de privacidad pública | Ruta `/privacidad` |
| Ser honesto sobre el modelo | Limitaciones enumeradas en el informe y en la UI | `INFORME.md` §3.3 y §6 |
| Verificar antes de afirmar | 84 tests + E2E + k6 + mediciones | `reports/Pruebas.md` |
| Declarar el uso de IA | Sección 3 de este documento | Este documento |

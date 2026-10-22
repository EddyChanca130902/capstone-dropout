# EarlySign · Informe del proyecto

**Signales tempranos de abandono académico**
Universidad Privada del Norte (UPN) · Proyecto de tesis T2

| | |
|---|---|
| **Producto** | EarlySign — sistema de alerta temprana para la orientación académica |
| **Institución** | Universidad Privada del Norte (UPN) |
| **Autor** | ⟨completar: nombre y apellido⟩ |
| **Asesor** | ⟨completar: nombre del asesor⟩ |
| **Fecha** | 21 de octubre de 2026 |
| **Repositorio** | https://github.com/EddyChanca130902/capstone-dropout |
| **Demo** | https://capstone-dropout.vercel.app |
| **Documentos relacionados** | [Plan de calidad](docs/PLAN_CALIDAD.md) · [Plan de seguridad](docs/PLAN_SEGURIDAD.md) · [Evaluación de la solución](docs/EVALUACION_SOLUCION.md) · [Ética, fuentes y uso de IA](docs/ETICA_Y_FUENTES.md) · [Guion de sustentación](docs/GUION_SUSTENTACION.md) · [Informe de pruebas](reports/Pruebas.md) |

> **Nota de uso:** los campos marcados con ⟨completar⟩ requieren datos de la UPN que el autor debe incorporar antes de la entrega.

---

## 1. Resumen ejecutivo

EarlySign es un sistema web que apoya la labor de la unidad de orientación y bienestar estudiantil: a partir de los datos que el orientador registra de cada estudiante, calcula la **probabilidad de abandono académico** y un **nivel de riesgo** (BAJO / MEDIO / ALTO) que permite priorizar a quién acompañar primero.

El sistema se sostiene sobre un modelo de aprendizaje automático (XGBoost) entrenado con el dataset público de la Universidad de Minho (Portugal), expuesto como servicio REST y consumido por una SPA de Angular. Los datos se almacenan en PostgreSQL con **aislamiento por usuario aplicado en la base de datos** (Row Level Security), no en el código.

**Resultados principales:**

| Indicador | Valor |
|---|---|
| AUC-ROC del modelo (test 20 % estratificado) | **0.934** |
| Recall sobre la clase Dropout | **0.831** |
| F1 / PR-AUC / Brier | 0.818 / 0.901 / 0.092 |
| Latencia de inferencia | **0.34 ms** (0.97 ms medidos en el servidor de producción) |
| Capacidad de la API | **371 req/s** con 200 VUs (0 % de errores) |
| Pruebas automatizadas | **72** unitarias + integración + E2E + carga |
| Corrección de un defecto que invalidaba el modelo | 6 de 13 variables del formulario **no influían** en la predicción |

---

## 2. Problemática

### 2.1 Contexto

En la UPN, la unidad de orientación recibe la demanda de acompañamiento de estudiantes que han acumulado dificultades académicas, arrears o problemas socioeconómicas durante el ciclo. La identificación de esos casos hoy depende de la **experiencia individual del orientador**: cuando un estudiante consulta, se evalúa el caso en ese momento.

### 2.2 Problema

Ese proceso tiene tres limitaciones estructurales:

1. **Detección tardía**: la alerta llega cuando el estudiante ya solicita ayuda; no hay un mecanismo que revise periódicamente a toda la población.
2. **Dependencia del criterio individual**: dos orientadores pueden priorizar de forma distinta ante el mismo expediente, y no queda registro de por qué se priorizó a quien se priorizó.
3. **Sin priorización**: cuando el volumen de casos supera la capacidad de atención, no existe un criterio objetivo y explicable para ordenar la cola de trabajo.

### 2.3 Necesidad

Un mecanismo que (a) transforme los datos que ya se registran en las tutorías en una **señal de riesgo comparable y trazable**, (b) ordene los casos con un criterio **cuantificable y explicable**, y (c) **no sustituya al orientador**: que le sirva de apoyo, no de decisión automática.

### 2.4 Usuarios y stakeholders

| Actor | Necesidad |
|---|---|
| Orientador académico | Priorizar la cola de acompañamiento y justificar la priorización |
| Unidad de orientación | Disponer de un tablero de indicadores de la población |
| Dirección de bienestar | Evidencia cuantitativa del riesgo de abandono por área y cohorte |
| Estudiante | Ser identificado a tiempo para recibir acompañamiento preventivo |
| Institución (UPN) | Cumplir la normativa de protección de datos personales |

---

## 3. Objetivos

### 3.1 Objetivo general

Desarrollar e implementar un sistema web de alerta temprana que estime la probabilidad de abandono académico de los estudiantes de la UPN y priorice el acompañamiento del orientador, con trazabilidad de las decisiones y respeto a la normativa de protección de datos.

### 3.2 Objetivos específicos

1. Construir y validar un modelo predictivo de abandono con métricas verificables y documentadas.
2. Implementar una API REST con autenticación, autorización por usuario y persistencia trazable.
3. Implementar una SPA con el flujo completo: registro de la evaluación, resultado, tablero de indicadores e historial.
4. Garantizar que el uso del sistema respeta la normativa de protección de datos personales.
5. Verificar el comportamiento del sistema bajo carga con pruebas de estrés reproducibles.

### 3.3 No objetivos (delimitación explícita)

- **No** se realiza ninguna decisión automatizada con efectos jurídicos sobre el estudiante.
- **No** se predice el desempeño académico, solo la condición de abandono.
- **No** se sustituye el criterio profesional del orientador.
- **No** se incorporan datos de terceros ni se comparte información fuera de la institución.

---

## 4. Alternativas evaluadas

Las decisiones se tomaron con una matriz de criterios ponderados (viabilidad técnica 30 %, ajuste al problema 30 %, costo 20 %, mantenibilidad 20 %).

### 4.1 Origen de los datos de entrenamiento

| Alternativa | Datos | Viabilidad | Problema | Decisión |
|---|---|---|---|---|
| **A. Dataset Perú (Dropout intentions)** | 768 filas × 88 variables | Alta | 177 filas sin target; 40+ ítems psicométricos que el formulario no captura; AUC 0.68 | ❌ Descartada |
| **B. UCI Portugal (Minho)** | 4 424 × 37 | Alta | Proxy: contexto educativo Portuguese | ✅ **Elegida** |
| **C. Datos propios de la UPN** | A construir | Baja | Requiere 2-3 años de cohortes; no viable en el plazo del proyecto | ❌ Descartada (fase futura) |

> La alternativa A se evaluó y se implementó parcialmente (notebook `03_modelo_peru.ipynb`, modelo `modelo_peru.joblib`) hasta demostrar su inviabilidad: **AUC 0.68 frente a 0.934**, con solo 591 filas utilizables. Se eliminó del producto y se documentó como línea de investigación futura.

### 4.2 Modelo de aprendizaje

| Alternativa | AUC | Recall (Dropout) | F1 | Decisión |
|---|---|---|---|---|
| Regresión Logística (class_weight balanced) | 0.932 | 0.838 | 0.814 | Alternativa de respaldo |
| Random Forest (300 árboles) | 0.934 | 0.792 | 0.811 | ❌ |
| **XGBoost** (300, depth 4, lr 0.05) | **0.934** | **0.831** | **0.818** | ✅ **Elegido** |

> XGBoost se eligió por **recall**: en un sistema de alerta temprana importa detectar más casos, aunque con más falsos positivos. La regresión logística queda a 0.002 de AUC con mucha menos complejidad: es la opción a reevaluar si se priorizara interpretabilidad.

### 4.3 Backend

| Alternativa | Encaje | Mantenibilidad | Decisión |
|---|---|---|---|
| **FastAPI (Python)** | Nativo del modelo (scikit-learn), OpenAPI automático, validación con Pydantic | Alta | ✅ **Elegido** |
| Django (Python) |ORM y admin útiles, pero pesado para una API | Media | ❌ |
| Flask (Python) | Ligero, sin validación de contratos ni async | Baja | ❌ |
| NestJS / Node | Tipado fuerte, pero duplicaría la lógica del modelo | Media | ❌ |

### 4.4 Frontend

| Alternativa | Encaje | Decisión |
|---|---|---|
| Streamlit (Python) | Prototipo T1, pero sin control de UX, sin routing real ni estados de carga finos | Se conserva como cliente de referencia |
| React / Vue | Válidos, pero menor ecosystemo de herramientas de formularios y signals | ❌ |
| **Angular 22** | Formularios reactivos, signals, guardas de ruta, interceptor con refresh, build optimizado | ✅ **Elegido** |

### 4.5 Base de datos y autenticación

| Alternativa | Decisión |
|---|---|
| SQLite local | Solo para el prototipo T1; sin concurrencia ni aislamiento por usuario |
| **Supabase (Postgres + Auth + RLS)** | Un solo servicio: base de datos con RLS, autenticación con JWT verificado en el servidor y panel de administración |
| Firebase | Modelo de datos NoSQL, sin RLS por fila |
| PostgreSQL + Auth0/Stytch | Más piezas que operar; coste mensual adicional |

### 4.6 Herramientas de prueba de carga

| Alternativa | Decisión |
|---|---|
| **k6** | Script en JavaScript (mismo lenguaje que el frontend), escenarios declarativos, umbrales como SLA y salida con código de error: se integra en CI |
| Locust | requiring Python, más indicado para lógica de negocio compleja |
| JMeter | Interfaz gráfica, poco automatizable |

### 4.7 Despliegue

| Alternativa | Decisión |
|---|---|
| **Render (API) + Vercel (frontend)** | Render tiene Dockerfile y healthcheck; Vercel detecta Angular nativamente. Coste cero en el plan gratuito |
| Railway / Fly.io | Equivalentes; Render se eligió por el blueprint (`render.yaml`) |
| Servidor propio UPN | Sin control del entorno ni del coste de mantenimiento |

---

## 5. Restricciones

| Tipo | Restricción | Impacto en el diseño |
|---|---|---|
| **Datos** | No existen datos históricos de la UPN con estas variables | El modelo es un **proxy**; se documenta el margen de error y se exige criterio humano |
| **Datos** | El dataset de entrenamiento no incluye datos peruanos | El mapeo de áreas es una simplificación explícita; el campo *Área* resultó poco informativo (importancia 0 en 2 de 5 áreas) |
| **Datos** | 23 de las 36 variables del modelo no las captura el formulario | Se imputan con la mediana del entrenamiento (`models/defaults.json`) |
| **Temporales** | Entrega en 2 etapas (T1 → T2) | El prototipo se priorizó; la migración a arquitectura de producción se ejecutó en T2 |
| **Presupuesto** | Servicios gratuitos | La API duerme tras 15 min sin tráfico: arranque en frío de ~20 s medido |
| **Regulatorias** | Protección de datos personales | RLS, minimización de datos, política de privacidad publicada, sin decisiones automatizadas |
| **Técnicas** | `supabase` 2.33.0 es incompatible consigo mismo | Se usa PostgREST directamente |
| **Técnicas** | Un `.joblib` no es portable entre versiones | Versiones pinneadas en `requirements.txt` y en la imagen Docker |

---

## 6. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación implementada | Estado |
|---|---|---|---|---|---|
| R1 | El modelo no generaliza a la población UPN (proxy de Portugal) | Alta | Alto | Se declara como estimación, nunca como veredicto; se exige validación del orientador; panel de resultados con disclaimer visible | Mitigado |
| R2 | Un dato mal codificado invalida la predicción en silencio | Media | **Muy alto** | Test de regresión que verifica que **cada** campo mueve la probabilidad; ruta rápida verificada contra el pipeline original con `atol=1e-9` | Mitigado |
| R3 | Fuga de datos entre orientadores | Baja | **Muy alto** | RLS en la base de datos (4 políticas) + verificador que crea dos usuarios y comprueba el aislamiento | Mitigado |
| R4 | Filtración de secretos en el repositorio | Media | Muy alto | `.env` en `.gitignore`, `.env.example` como plantilla, claves en el gestor de secretos de Render, `service_role` solo en servidor | Mitigado |
| R5 | El servicio gratuito se duerme y falla en una demostración | Alta | Medio | Healthcheck, caché de sesiones de 60 s, despliegue en < 3 min; plan pago como recomendación | **Pendiente: plan Starter** |
| R6 | Caída de Supabase deja la API sin persistencia | Media | Alto | El healthcheck reporta el estado de Supabase; el modelo sigue respondiendo sin persistencia | Mitigado |
| R7 | Sesiones de login bloqueadas por límite de tasa de Supabase | Media | Medio | Caché de sesiones de 60 s indexada por hash + traducción del límite a HTTP 429 | Mitigado |
| R8 | Desfase entre el reloj del servidor y el de Supabase | Media | Medio | `leeway` de 300 s en la validación de JWT (se midieron 4 min de desfase) | Mitigado |
| R9 | Regresión silenciosa al cambiar el preprocesado | Media | Alto | La ruta rápida se valida contra el pipeline de sklearn en cada ejecución de tests | Mitigado |
| R10 | Los datos de entrada no quedan auditados | Baja | Medio | `entradas` (JSONB), `modelo_version` y marcas de tiempo en cada evaluación | Mitigado |

---

## 7. Herramientas y entorno

| Capa | Herramienta | Versión | Justificación de la elección |
|---|---|---|---|
| Datos y modelo | Python | 3.11.9 | Ecosistema científico estándar (scikit-learn, XGBoost, SHAP) |
| | pandas / numpy | 3.0.6 / 2.4.6 | Manipulación de las 4 424 × 37 del dataset |
| | scikit-learn | 1.9.1 | Pipeline de preprocesado serializable en un único artefacto |
| | XGBoost | 3.2.0 | Mejor recall de la clase de interés entre las tres alternativas evaluadas |
| | SHAP | 0.51.0 | Interpretabilidad: 7 figuras de explicabilidad global y local |
| | joblib | 1.6.0 | Serialización del pipeline con metadatos de versión |
| API | FastAPI | 0.156.0 | Contratos tipados, OpenAPI automático, async |
| | Uvicorn | 0.54.0 | Servidor ASGI |
| | Pydantic / pydantic-settings | 2.14.1 / 2.16.1 | Validación y configuración desde `.env` |
| | PyJWT / cryptography | 2.15.1 / 50.0.2 | Verificación local de JWT ES256 con JWKS |
| | PostgREST (Python) | 2.33.0 | Acceso a los datos con conexiones persistentes |
| | httpx | 0.28.1 | Cliente HTTP con timeouts configurables |
| Frontend | Angular | 22.2 | Formularios reactivos, signals, guardas, interceptor |
| | TypeScript | ~6.0 | Tipado estricto de los contratos con la API |
| | Vitest | 5.0 | Runner de tests integrado en el builder de Angular |
| Datos | Supabase (Postgres 17 + Auth) | cloud | RLS por fila, JWT, panel de administración |
| Calidad | pytest | 9.1.1 | Fixtures y parametrización |
| | k6 | 2.0.0 | Escenarios declarativos con umbrales como SLA |
| | Playwright + Edge | — | Recorrido E2E con capturas y detección de errores de consola |
| Despliegue | Docker | 29.4 | Imagen reproducible con versiones pinneadas |
| | Render | — | Blueprint con healthcheck |
| | Vercel | — | Preset Angular, sin configuración adicional |
| | GitHub Actions | — | CI: pytest → Vitest → build → smoke de k6 |

---

## 8. Metodología

### 8.1 Modelo de desarrollo

Ciclo iterativo por etapas, con dos entregables formales (T1 y T2):

```
T1 (prototipo)                      T2 (sistema)
─────────────────────────────      ─────────────────────────────
Streamlit + SQLite local      ──►  FastAPI + Supabase + Angular
Predicción sin persistencia         Persistencia con RLS y auditoría
1 notebook de modelado              2 notebooks + scripts reproducibles
Sin autenticación                   Supabase Auth + JWT verificado
Sin pruebas automatizadas            72 tests + carga + E2E
```

### 8.2 Metodología de modelado (CRISP-DM adaptada)

1. **Comprensión del negocio**: interviews con el orientador, definición del problema y del criterio de éxito.
2. **Comprensión de datos**: EDA automatizado (`01_eda.ipynb`): distribución del target, 37 variables, 0 nulos, 0 duplicados; análisis de factores binarios, notas vs. abandono y correlaciones (7 figuras en `reports/figures/`).
3. **Preparación**: mapeo de variables a texto legible, imputación de nulos (0 en este dataset), construcción del target binario (`Dropout` vs. resto) y persistencia en `data/processed/data_clean.csv`.
4. **Modelado**: tres modelos con la misma partición estratificada, preprocesado encapsulado en un `Pipeline` y comparación de métricas (`02_modeling.ipynb`).
5. **Evaluación**: train/test 80/20 estratificado + validación cruzada de 5 folds; ablation study del efecto del 2.º semestre; calibración de umbrales; interpretabilidad con SHAP.
6. **Despliegue**: empaquetado del pipeline en `modelo_final.joblib` con versión, perfil de imputación en `models/defaults.json` y script reproducible (`scripts/build_defaults.py`).
7. **Mantenimiento**: el perfil de imputación se regenera desde el dataset; los tests de regresión detectan cualquier divergencia entre la ruta rápida y el pipeline original.

### 8.3 Metodología de verificación

Pirámide de pruebas con 4 niveles (ver [Plan de calidad](docs/PLAN_CALIDAD.md)):

```
        /\        E2E en producción (6 pantallas, 0 errores de consola)
       /  \       Carga y estrés (k6: 200 VUs)
      /    \      Integración contra Supabase real
     /______\     Unitarias (59 pytest + 13 Vitest)
```

---

## 9. Diseño

### 9.1 Arquitectura

```
Angular 22 (Vercel)  ──HTTPS + Bearer JWT──►  FastAPI (Render, Docker)
   login · panel · evaluar                      │
   historial · privacidad                       ├── services/model.py   singleton .joblib
                                                ├── services/supabase.py  PostgREST (keep-alive)
                                                ├── core/security.py    JWT con JWKS cacheado
                                                └── core/sesion_cache.py cache 60 s
                                                         │
                                                         ▼
                                          Supabase (Postgres + Auth + RLS)
```

### 9.2 Modelo de datos

```sql
evaluaciones (
  id              bigint identity PRIMARY KEY,
  user_id         uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  dni             text NOT NULL,
  nombre          text NOT NULL,
  area_estudios   text NOT NULL,
  probabilidad    numeric(5,4) NOT NULL CHECK (probabilidad BETWEEN 0 AND 1),
  nivel           text NOT NULL CHECK (nivel IN ('BAJO','MEDIO','ALTO')),
  modelo_version  text NOT NULL,     -- trazabilidad del modelo
  entradas        jsonb NOT NULL,    -- snapshot de las entradas
  creado_en       timestamptz NOT NULL DEFAULT now(),
  actualizado_en  timestamptz NOT NULL DEFAULT now()
)
-- Índices: (user_id, creado_en DESC), dni, nivel
-- RLS: 4 políticas sobre auth.uid() = user_id
```

### 9.3 API

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `GET` | `/health` | — | Estado del servicio, del modelo y de Supabase |
| `POST` | `/api/v1/auth/login` | — | Login (Supabase Auth + caché de 60 s) |
| `POST` | `/api/v1/auth/refresh` | — | Renovación de token |
| `GET` | `/api/v1/auth/me` | ✅ | Perfil del usuario |
| `POST` | `/api/v1/predict` | opcional | Infiere **sin persistir** (usado por k6) |
| `POST` | `/api/v1/evaluaciones` | ✅ | Infiere y guarda |
| `GET` | `/api/v1/evaluaciones` | ✅ | Historial paginado y filtrable |
| `GET/PATCH/DELETE` | `/api/v1/evaluaciones/{id}` | ✅ | Detalle, corrección, borrado |
| `GET` | `/api/v1/dashboard/resumen` | ✅ | Indicadores del panel |

### 9.4 Interfaz de usuario

| Pantalla | Función |
|---|---|
| `/login` | Autenticación con mensajes accionables en español y enlace a la política de privacidad |
| `/panel` | 4 indicadores, distribución por nivel, riesgo por área, tabla de recientes |
| `/evaluar` | Formulario de 2 pasos con indicador de progreso, validación en cliente y resultado con semáforo |
| `/historial` | Filtros por área y nivel, corrección manual del nivel, borrado con confirmación |
| `/privacidad` | Política completa, accesible sin autenticación |

Estados implementados: carga (esqueletos), vacío (con acción), error (con reintento), hover y confirmación (toasts).

---

## 10. Plan de desarrollo

El historial de 11 commits documenta la trazabilidad del proyecto:

| Hito | Entregable | Evidencia |
|---|---|---|
| H1 · Análisis y prototipo | EDA, 3 modelos comparados, dashboard Streamlit | `notebooks/`, `reports/figures/` |
| H2 · Corrección del núcleo | Codificación canónica, imputación por medianas, tests de regresión | `src/predictor.py`, `tests/test_predictor.py` |
| H3 · Migración de arquitectura | FastAPI, Supabase, RLS, Angular, k6 | `api/`, `frontend/`, `k6/`, `supabase/` |
| H4 · Calidad y rendimiento | Cache del JWKS, ruta rápida, caché de sesiones, 72 tests | `reports/Pruebas.md` |
| H5 · Despliegue | Docker, Render, Vercel, CI | `Dockerfile`, `render.yaml`, `frontend/vercel.json`, `.github/` |
| H6 · Rediseño de interfaz | Privacidad, empty/loading states, hover, iconos SVG | `frontend/src/app/shared/`, `features/privacidad/` |
| H7 · Documentación de evaluación | Informes, planes, guion de sustentación | `INFORME.md`, `docs/` |

Metodología de trabajo: un commit por unidad funcional, con mensaje que explica el *porqué* y referencia el problema que resuelve. El historial completo está en `git log`.

---

## 11. Coherencia entre el informe y el software

Cada apartado del informe se corresponde con ficheros verificables del repositorio:

| Apartado del informe | Implementación en el repositorio | Verificación |
|---|---|---|
| Problema y objetivos (§2, §3) | Producto desplegado y funcional | Demo en producción |
| Alternativas (§4) | `notebooks/02_modeling.ipynb` (comparativa de modelos), `notebooks/03_modelo_peru.ipynb` (evidencia del descarte de Perú) | Ejecutable |
| Restricciones y riesgos (§5, §6) | `src/predictor.py` (imputación), `supabase/migrations/0001_init.sql` (RLS), `api/core/sesion_cache.py` | Tests + verificador |
| Herramientas (§7) | `requirements.txt`, `requirements-api.txt`, `requirements-dev.txt`, `frontend/package.json` | Versiones exactas |
| Metodología de modelado (§8.2) | `notebooks/01_eda.ipynb`, `notebooks/02_modeling.ipynb`, `scripts/build_defaults.py` | Reproducible |
| Metodología de verificación (§8.3) | `tests/`, `frontend/src/**/*.spec.ts`, `k6/`, `.github/workflows/ci.yml` | CI en cada push |
| Diseño de arquitectura (§9.1) | `api/main.py`, `api/core/`, `api/services/` | Ejecutable |
| Diseño de datos (§9.2) | `supabase/migrations/0001_init.sql` | `scripts/verify_supabase.py` |
| Diseño de la API (§9.3) | `api/routers/`, `api/schemas/` | OpenAPI en `/docs` |
| Diseño de la interfaz (§9.4) | `frontend/src/app/features/` | Recorrido E2E con capturas |
| Plan de desarrollo (§10) | Historial de commits | `git log` |
| Figuras de pruebas | [índice de figuras](docs/FIGURAS_PRUEBAS.md) | `reports/figures/08` a `11` |
| Política de privacidad | `frontend/src/app/features/privacidad/` | Ruta `/privacidad` |

---

| Indicadores y evaluación | [ñdice de evaluación](docs/EVALUACION_SOLUCION.md) § 1 bis | Cada afirmación del software tiene un KPI que la respalda |

## 12. Resultados verificados

| Ámbito | Resultado | Evidencia |
|---|---|---|
| Modelo | AUC 0.934, recall 0.831 | `notebooks/02_modeling.ipynb` |
| Pruebas unitarias | 72 tests, 0 fallos | `reports/Pruebas.md` |
| Carga | 371 req/s con 200 VUs, p95 112 ms | `reports/Pruebas.md` |
| Producción | 44 req/s, p95 5.7 s, 3.2 % de errores (límite del plan gratuito) | `reports/Pruebas.md` |
| E2E | 6 pantallas, 0 errores de consola | Capturas de Playwright |
| Aislamiento | Verificado con dos usuarios reales | `scripts/verify_supabase.py` |
| Latencia de inferencia | 0.34 ms local / 0.97 ms en producción | Respuesta de la propia API |

---

## 13. Conclusiones y trabajo futuro

**Conclusiones**

1. EarlySign cumple su propósito: transforma registros de orientación en una señal de riesgo cuantificada, trazable y explicable.
2. El principal aporte técnico no es el modelo (0.934 de AUC es un resultado esperado en este dataset), sino la **corrección del contrato entre el formulario y el modelo**: sin ella, 6 de 13 variables se descartaban en silencio y el sistema habría funcionado, aunque con apariencia de funcionar.
3. El aislamiento de datos en la base de datos (RLS) y la trazabilidad de cada evaluación (`entradas` + `modelo_version`) son lo que convierten un modelo en un sistema utilizable por una institución.

**Trabajo futuro**

| Prioridad | Acción | Impacto esperado |
|---|---|---|
| Alta | Migrar el proyecto de Supabase a la región de la UPN | Latencia de 300 ms → < 60 ms en el historial |
| Alta | Plan de hosting pago | Elimina el arranque en frío y el 3,2 % de errores |
| Media | Validación del modelo con datos de la UPN (2-3 cohortes) | Convierte el proxy en modelo propio |
| Media | Calibración de umbrales según capacidad de atención | Distribución de niveles coherente con los recursos |
| Media | Versión "alerta temprana" (solo 1.er semestre) | Detección un semestre antes (AUC 0.907) |
| Baja | Ampliar el formulario con 3 variables de alto impacto | Menor error individual de la predicción |
| Baja | Migrar a un modelo calibrado y comparar con regresión logística | Interpretabilidad a cambio de ~0.002 de AUC |

---

## 14. Referencias

1. UCI Machine Learning Repository. *Predict Students' Dropout and Academic Success*. Universidade de Minho, 2021. <https://doi.org/10.24432/C5BW9Q>
2. Chen, T. y Guestrin, C. (2016). *XGBoost: A Scalable Tree Boosting System*. KDD '16.
3. Harris, C. et al. (2020). *Array programming with NumPy*. Nature 585, 357-362.
4. McKinney, W. (2010). *Data Structures for Statistical Computing in Python*. SciPy 2010.
5. Pedregosa, F. et al. (2011). *Scikit-learn: Machine Learning in Python*. JMLR 12, 2825-2830.
6. Lundberg, S. y Lee, S.-I. (2017). *A Unified Approach to Interpreting Model Predictions*. NeurIPS.
7. FastAPI. *Documentation*. <https://fastapi.tiangolo.com>
8. Angular. *Documentation*. <https://angular.dev>
9. Supabase. *Documentation: Row Level Security, Auth*. <https://supabase.com/docs>
10. Grafana. *k6 documentation*. <https://k6.io/docs/>
11. PostgreSQL Global Development Group. *Row Security Policies*. Documentación oficial.
12. OWASP Foundation. *OWASP Top 10* y *ASVS v4.0*.

> El uso de herramientas de inteligencia artificial durante el desarrollo se declara en [Ética, fuentes y uso de IA](docs/ETICA_Y_FUENTES.md).

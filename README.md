# AlertaTemprana · Predicción de riesgo de abandono universitario

Sistema de alerta temprana para orientar el acompañamiento académico: a partir de los
datos que registra el orientador, estima la probabilidad de abandono de un estudiante y
prioriza los casos que requieren seguimiento.

**Stack actual:** Angular 22 (frontend) · FastAPI (backend) · Supabase (Postgres + Auth) ·
XGBoost (modelo) · k6 (pruebas de carga) · pytest + Vitest (pruebas unitarias).

> El dashboard en Streamlit (`dashboard/`) se conserva como **cliente de referencia**
> (comparar predicciones, trabajar sin conexión). El producto vigente es
> Angular + FastAPI + Supabase.

---

## 1. Puesta en marcha

### 1.1 Requisitos

- Python 3.11 (venv ya creado en `dropout-env/`)
- Node 20+ (para Angular)
- Docker (opcional, para el despliegue)
- k6 (opcional, para las pruebas de carga)

### 1.2 Dependencias

```powershell
# Backend
.\dropout-env\Scripts\python.exe -m pip install -r requirements.txt
.\dropout-env\Scripts\python.exe -m pip install -r requirements-dev.txt

# Frontend
cd frontend
npm install
```

### 1.3 Configuración (.env)

Copia `.env.example` a `.env` y completa:

```powershell
Copy-Item .env.example .env
```

| Variable | Para qué sirve |
|---|---|
| `SUPABASE_URL` | URL base del proyecto **sin** `/rest/v1` (la API la normaliza si viene con el sufijo) |
| `SUPABASE_ANON_KEY` | Clave pública. Se usa con el JWT del usuario para que aplique RLS |
| `SUPABASE_SERVICE_ROLE_KEY` | Clave de servicio: **solo servidor** (migraciones, semilla) |
| `TEST_USER_EMAIL` / `TEST_USER_PASSWORD` | Usuario de pruebas (k6 e integración) |

> `SUPABASE_KEY` se acepta como alias histórico de ambas claves.

### 1.4 Esquema de Supabase (paso pendiente ⚠️)

El proyecto de Supabase está creado y la tabla `evaluaciones` existe, pero **le falta la
migración** que añade `user_id`, `modelo_version`, `entradas`, RLS y los índices.

```powershell
.\dropout-env\Scripts\python.exe scripts\apply_migrations.py
```

El script intenta aplicarla sola si define `SUPABASE_ACCESS_TOKEN` (Management API) o
`SUPABASE_DB_URL` (Postgres directo). Si no, imprime el SQL para pegarlo en
**Supabase → SQL Editor → New query → Run**:

```
supabase/migrations/0001_init.sql
```

**Qué cambia al aplicarla:**

- `evaluaciones` gana `user_id`, `modelo_version`, `entradas`, `creado_en`, `actualizado_en`.
- Se activa **Row Level Security**: cada orientador solo ve y modifica sus propias
  evaluaciones. Hasta aplicarla, la API opera con la clave de servicio y el aislamiento
  por usuario se aplica en el código (en `api/services/evaluaciones.py`).

### 1.5 Usuario de prueba

```powershell
.\dropout-env\Scripts\python.exe scripts\seed_user.py --email orientador@alertatemprana.pe --password "TuClaveFuerte"
```

### 1.6 Configuracion del frontend

`frontend/src/environments/` define la URL de la API:

- `environment.ts` -> build de produccion (`https://api.alertatemprana.pe/api/v1`)
- `environment.development.ts` -> `http://localhost:8000/api/v1` (usada por `ng serve`)

La sustitucion automatica esta en `frontend/angular.json` (`fileReplacements`).
Para desplegar, cambia la URL de `environment.ts` (o parametrizala en el build).

### 1.7 Arranancar

```powershell
# API (http://localhost:8000/docs)
.\dropout-env\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000

# Frontend (http://localhost:4200)
cd frontend
npm start

# Dashboard legacy en Streamlit (opcional, http://localhost:8501)
.\dropout-env\Scripts\python.exe -m streamlit run dashboard/app.py
```

O todo junto: `.\scripts\dev.ps1`

---

## 2. Arquitectura

```
Angular 22 (SPA)  ──HTTPS + JWT──>  FastAPI (Python 3.11)
   login · panel                     │
   evaluar (2 pasos)                 ├── models/modelo_final.joblib  (singleton en memoria)
   historial (CRUD)                  ├── models/defaults.json       (perfil de imputación)
                                     └── Supabase (Postgres + Auth + RLS)
```

### Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado del servicio y del modelo (lo usa k6) |
| `GET` | `/api/v1` | Índice de endpoints |
| `POST` | `/api/v1/auth/login` | Inicia sesión contra Supabase Auth y devuelve los tokens |
| `POST` | `/api/v1/auth/refresh` | Renueva el access token |
| `GET` | `/api/v1/auth/me` | Perfil del usuario autenticado |
| `POST` | `/api/v1/predict` | **Infiere sin persistir** (ideal para k6) |
| `POST` | `/api/v1/evaluaciones` | Infiere y guarda |
| `GET` | `/api/v1/evaluaciones` | Historial paginado y filtrable |
| `GET/PATCH/DELETE` | `/api/v1/evaluaciones/{id}` | Detalle, corrección y borrado |
| `GET` | `/api/v1/dashboard/resumen` | Métricas del panel |

La documentación interactiva está en `http://localhost:8000/docs`.

### Seguridad

- Contraseñas en **Supabase Auth** (hash gestionado por Supabase).
- El backend valida la firma del JWT **localmente** con el JWKS cacheado
  (`api/core/security.py`), sin llamadas de red por petición.
- `leeway` de 300 s al validar `iat`: absorbe el desfase entre el reloj local y el
  servidor (en este equipo se llegó a medir **4 minutos** de diferencia, lo que
  invalidaba todos los tokens).
- `SUPABASE_SERVICE_ROLE_KEY` nunca llega al navegador; `SUPABASE_ANON_KEY` sí, pero con
  RLS la base de datos es la que autoriza.
- El `.env` está en `.gitignore`. **Rota las claves** si alguna vez se versionó.

---

## 3. El modelo

| | |
|---|---|
| Algoritmo | XGBoost (`n_estimators=300`, `max_depth=4`, `learning_rate=0.05`) |
| Pipeline | `ColumnTransformer` (StandardScaler + One-Hot) → `XGBClassifier` |
| Entrenamiento | UCI "Predict students' dropout and academic success" (Portugal), 4 424 filas |
| Target | `Dropout` vs resto (32.1 % positivos) |
| Test split | 20 % estratificado, `random_state=42` |
| **AUC-ROC** | **0.934** |
| Recall (Dropout) | 0.831 |
| F1 (Dropout) | 0.818 |
| Brier | 0.092 |
| Umbrales | ALTO > 0.60 · MEDIO > 0.35 |

### Reconstruir el modelo

```powershell
# 1. EDA + limpieza          -> data/processed/data_clean.csv
jupyter lab  ->  notebooks/01_eda.ipynb, notebooks/02_modeling.ipynb
# 2. Perfil de imputación    -> models/defaults.json
.\dropout-env\Scripts\python.exe scripts\build_defaults.py
```

### Por qué existe `models/defaults.json`

El formulario recoge 13 variables, pero el modelo espera las 36 del entrenamiento. Las 23
restantes se imputan con la **mediana (o moda) del entrenamiento**, no con `0`:
rellenar con cero lasmetía al estudiante en un perfil irreal (nota de admisión 0, PIB 0…)
y sesgaba la predicción.

### Limitaciones conocidas

1. **El modelo es un proxy de Portugal.** Se entrenó con datos portugueses; el mapeo de
   áreas de estudio es una simplificación explícita (5 áreas genéricas → 5 carreras
   portugueses). No hay datos peruanos equivalentes con estas variables.
   *Detalle:* el arbol **no usa** las categorias `Nursing` ni `Management` (importancia 0),
   asi que cambiar el area solo altera la prediccion para "Arte y Diseno"
   (-> Animation & Multimedia, 6.9 % de importancia) y, en menor medida, "Ciencias Sociales
   y Humanidades" (-> Social Service, 1.4 %). El campo *Area* es hoy poco informativo.
2. **El formulario solo captura 13 de 36 variables.** Las variables no capturadas más
   influyentes son `Curricular units 2nd sem (credited)`, `Mother's occupation` y
   `Application mode`: añadirlas al formulario reduciría el error individual.
3. **La banda MEDIO es estrecha** (0.35–0.60): con el test split, solo el 9 % de los
   estudiantes cae en ella. Los umbrales son arbitrarios; conviene calibrarlos según la
   capacidad real de atención del orientador.
4. **No es "alerta temprana" en sentido estricto**: el formulario pide notas de los dos
   semestres. La ablación muestra que sin el 2.º semestre el AUC baja de 0.936 a 0.914
   (y el recall de 0.761 a 0.690) — hay margen para un modelo realmente temprano.
5. `Enrolled` se trata como "no abandono": 794 filas con etiqueta ambigua.

---

## 4. Pruebas

### 4.1 Unitarias y de integración (pytest)

```powershell
.\dropout-env\Scripts\python.exe -m pytest -q                       # todo
.\dropout-env\Scripts\python.exe -m pytest -q -m "not integration"   # sin red
```

| Fichero | Qué cubre |
|---|---|
| `tests/test_predictor.py` | 34 tests: contrato del formulario, **cada campo debe mover la predicción**, validaciones, equivalencia exacta de la ruta rápida con el pipeline original |
| `tests/test_api.py` | 16 tests: health, contrato de la API, validaciones, rutas protegidas, y un flujo completo contra Supabase (login → CRUD → panel) |

> El test `test_cada_campo_altera_la_probabilidad` es la red de seguridad del bug
> principal que se corrigió (ver §5).

### 4.2 Unitarias del frontend (Vitest)

```powershell
cd frontend
npm test
```

### 4.3 Carga y rendimiento (k6)

```powershell
$env:BASE_URL = "http://127.0.0.1:8000"
$env:TEST_EMAIL = "orientador@alertatemprana.pe"
$env:TEST_PASSWORD = "..."

k6 run k6/smoke.js     # 1 VU, 30 s: correctitud funcional
k6 run k6/load.js      # ramp 10 -> 50 VUs: capacidad
k6 run k6/stress.js    # hasta 200 VUs: punto de ruptura
k6 run k6/soak.js      # 30 min a 10 VUs: fugas y degradacion
```

**Resultados medidos en este equipo (12 núcleos, API en local):**

| Escenario | Resultado |
|---|---|
| `smoke` | 8/8 checks OK, 0 % errores |
| `load` (50 VUs) | **p95 = 10.5 ms**, p99 < 15 ms, 0 % errores, 100 % checks |
| `stress` (200 VUs) | ~370 req/s, p95 = 110 ms, 0 % errores |
| Inferencia pura (sin HTTP) | 0.34 ms por predicción, ~2 500 pred/s con 1 hilo |

> k6 mide **carga y rendimiento**, no corrección de la lógica: eso lo cubren pytest y
> Vitest. Para el flujo de UI usa Playwright.

---

## 5. Correcciones importantes aplicadas

| # | Problema | Impacto | Estado |
|---|---|---|---|
| 1 | Las categorías se enviaban como `"1"/"0"` y códigos de carrera, pero el encoder esperaba `"Male"/"Female"`, `"Yes"/"No"` y nombres de carrera. Con `handle_unknown="ignore"` se descartaban **en silencio** | 6 de 13 variables del formulario **no influían** en la predicción | ✅ Corregido en `src/predictor.py` + test que lo blinda |
| 2 | Las 23 variables no capturadas se rellenaban con `"0"` | Perfil de estudiante irreal → predicción sesgada | ✅ Imputación con medianas (`models/defaults.json`) |
| 3 | `.env` con la URL de Supabase terminada en `/rest/v1` | URLs inválidas en el SDK | ✅ Normalizado en `api/core/config.py` |
| 4 | El JWKS se descargaba **en cada request** | +300 ms por petición | ✅ Cliente cacheado (`api/core/security.py`) |
| 5 | Desfase de 4 min entre el reloj local y Supabase | Todos los tokens inválidos (401) | ✅ `leeway=300 s` |
| 6 | `supabase` 2.33.0 incompatible con su propio `ClientOptions` | La API no arrancaba | ✅ Se usa PostgREST directamente |
| 7 | `sklearn` gastaba ~5 ms en validar un DataFrame de 1 fila | 10.7 ms por predicción | ✅ Ruta rápida verificada contra el pipeline (p95: 646 ms → 10.5 ms con 50 VUs) |
| 8 | Contraseñas en texto plano en SQLite | Robo de credenciales trivial | ✅ Hash argon2 + migración del existente |
| 9 | RLS sin políticas rompía las escrituras | La API no podía guardar evaluaciones | ✅ Detección del esquema + migración preparada |
| 10 | `requirements.txt` era un `pip freeze` de 140 paquetes en UTF-16 (incluía torch) | Instalación lenta e incompleta | ✅ Dependencias curadas en UTF-8 |

---

## 6. Estructura del proyecto

```
capstone-dropout/
├── api/                      # FastAPI
│   ├── main.py               # create_app, CORS, lifespan
│   ├── core/                 # config, security (JWT), 
│   ├── schemas/              # contratos Pydantic
│   ├── services/             # model, supabase, evaluaciones (repositorio)
│   └── routers/              # auth, predict, evaluaciones, dashboard
├── src/                      # nucleo de inferencia (compartido con Streamlit)
│   ├── predictor.py          # transformador rapido + validaciones
│   └── database.py           # SQLite legacy con argon2
├── frontend/                 # Angular 22
│   └── src/app/
│       ├── core/             # api.service, auth.service, interceptor, guard
│       ├── features/         # login, dashboard, evaluar, historial
│       └── shared/           # shell, risk-badge
├── k6/                       # escenarios de carga
├── models/                   # modelo entrenado + defaults.json
├── data/                     # raw / processed / db local
├── notebooks/                # 01_eda, 02_modeling
├── scripts/                  # build_defaults, apply_migrations, seed_user, dev
├── supabase/migrations/      # 0001_init.sql
└── tests/                    # pytest
```

---

## 7. Pendientes

1. **Aplicar `supabase/migrations/0001_init.sql`** (§1.4) → activa RLS y el aislamiento
   por usuario.
2. Añadir `SUPABASE_ANON_KEY` real al `.env` (hoy se usa la clave de servicio como
   respaldo).
3. Rotar las claves de Supabase si el `.env` llegó a compartirse.
4. Calibrar los umbrales ALTO/MEDIO según la capacidad real del orientador.
5. Decidir si el modelo se queda en 2 semestres o se publica una variante de "alerta
   temprana" solo con el 1.er semestre.
6. Desplegar: Dockerfiles ya incluidos (`Dockerfile`, `frontend/Dockerfile`).

---

## 8. Despliegue

El sistema tiene dos piezas que se despliegan por separado:

| Pieza | Plataforma | Configuracion |
|---|---|---|
| Frontend (Angular 22) | **Vercel** | `frontend/vercel.json` |
| API (FastAPI) | **Render** / Railway / Fly.io | `Dockerfile` + `render.yaml` |

### 8.1 API (Render)

1. Sube el repositorio a GitHub.
2. En Render: **New > Blueprint** -> selecciona el repositorio. Render lee `render.yaml`
   y crea el servicio usando el `Dockerfile` de la raiz.
3. Configura las variables de entorno:

   | Variable | Valor |
   |---|---|
   | `CORS_ORIGINS` | `https://tu-frontend.vercel.app` |
   | `SUPABASE_URL` | `https://TU-PROYECTO.supabase.co` |
   | `SUPABASE_ANON_KEY` | clave publica de Supabase |
   | `SUPABASE_SERVICE_ROLE_KEY` | clave de servicio (solo servidor) |

4. Render te dara una URL del tipo `https://alertatemprana-api.onrender.com`. Verifica:
   `https://alertatemprana-api.onrender.com/health` -> `"estado": "ok"`.

> El `Dockerfile` ya fija `OMP_NUM_THREADS=1` (evita la sobrecoste de hilos de
> XGBoost bajo concurrencia) y las versiones criticas van pinneadas en
> `requirements.txt`, porque un `.joblib` no es portable entre versiones.

### 8.2 Frontend (Vercel)

1. En Vercel: **Add New > Project** -> importa el repositorio.
2. **Root Directory**: `frontend` (importante).
3. Vercel detecta Angular por `frontend/vercel.json`. Verifica que:
   - Build Command: `npm run build`
   - Output Directory: `dist/frontend/browser`
4. En **Settings > Environment Variables** anade:

   | Variable | Valor |
   |---|---|
   | `API_URL` | `https://alertatemprana-api.onrender.com/api/v1` |

   El build ejecuta `node scripts/configure-api-url.mjs`, que escribe esa URL en
   `src/environments/environment.ts` antes de compilar. **No hace falta tocar el
   codigo** para cambiar de API.

5. Tras desplegar, vuelve a Render y actualiza `CORS_ORIGINS` con la URL de Vercel
   (`https://tu-frontend.vercel.app`) y vuelve a desplegar la API.

### 8.3 Checklist antes de publicar

- [ ] `SUPABASE_ANON_KEY` y `SUPABASE_SERVICE_ROLE_KEY` son las reales (no las de prueba).
- [ ] Claves de Supabase rotadas si el `.env` se compartio alguna vez.
- [ ] Contrasena del usuario de prueba cambiada.
- [ ] `CORS_ORIGINS` con el dominio exacto del frontend (sin barra final).
- [ ] `pytest -q` y `k6 run k6/smoke.js` en verde contra la API desplegada.

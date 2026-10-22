# Plan de seguridad · EarlySign

**Criterio de evaluación:** 4. Seguridad y condiciones de funcionamiento
**Versión:** 1.0 · 21 de octubre de 2026 · UPN
**Alcance:** EarlySign (frontend Angular, API FastAPI, base de datos Supabase)

---

## 1. Contexto y alcance

EarlySign procesa **datos personales de estudiantes** (identificativos, sociodemográficos y académicos) para estimar el riesgo de abandono. Por tanto, la seguridad no es un añadido: es un requisito funcional.

Este plan cubre:

- **En alcance:** la aplicación web (frontend, API y base de datos), el modelo de aprendizaje automático, el proceso de despliegue, la gestión de secretos y los requisitos de instalación y ejecución.
- **Fuera de alcance:** la seguridad física de los servidores (responsabilidad de los proveedores), el hardening del sistema operativo de los proveedores (gestionado por Render y Supabase) y las políticas internas de la UPN sobre custodia de expedientes.

---

## 2. Inventario de activos

| # | Activo | Clasificación | Dónde vive |
|---|---|---|---|
| A1 | Datos personales de estudiantes (DNI, nombre, edad, género, área, situación económica y notas) | **Crítico / dato personal** | PostgreSQL (Supabase) |
| A2 | Tokens de sesión (JWT) | Alto | LocalStorage del navegador (cliente) |
| A3 | Clave de servicio de Supabase (`service_role`) | **Crítico** | Gestor de secretos de Render |
| A4 | Clave pública (`anon`) | Medio | Gestor de secretos + bundle del navegador |
| A5 | Modelo entrenado (`.joblib`) y perfil de imputación | Medio | Repositorio y contenedor |
| A6 | Contraseñas de los orientadores | **Crítico** | Supabase Auth (hash gestionado por Supabase) |
| A7 | Credenciales de la base de datos local heredada (SQLite) | Alto | `data/sistema_orientacion.db` (ignorada por git) |
| A8 | Logs de la API | Medio | Salida estándar de Render |

---

## 3. Modelo de amenazas

Metodología: STRIDE simplificado por flujo de datos.

```
Navegador ──HTTPS──► API ──TLS──► Supabase Auth / PostgREST
   │                    │
   │                    └──► Modelo en memoria (solo lectura)
   └──► localStorage (token)
```

| # | Amenaza | Vector | Activo | Severidad | Control |
|---|---|---|---|---|---|
| T1 | Interceptación de credenciales | Red insegura, XSS | A2, A6 | **Crítica** | HTTPS/TLS en todas las capas; tokens en `localStorage` (no en cookies, sin acceso a `HttpOnly`); CSP y cabeceras de seguridad en Vercel; sanitización de toda salida en Angular (interpolación por defecto escapa HTML) |
| T2 | Acceso a datos de otro orientador | IDOR / fallo de autorización | **A1** | **Crítica** | **RLS en PostgreSQL**: 4 políticas `auth.uid() = user_id`. El aislamiento lo aplica la base de datos, no el código: un error en la API no expone datos ajenos |
| T3 | Filtración de la clave de servicio | Repositorio, logs, bundle | **A3** | **Crítica** | Clave solo en el servidor (Render Secrets); `.env` y `*.db` en `.gitignore`; `service_role` nunca en el bundle del navegador; verificación en CI de que no haya secretos versionados |
| T4 | Escalada de privilegios | Token manipulado, `alg: none` | A2, A1 | Alta | Verificación **local** de la firma (JWKS de Supabase, clave ES256/RS256, `kid` correspondente); se validan `exp`, `iat` (con `leeway` de 300 s), `aud` y `sub`; el `role` del token no se usa para autorizar |
| T5 | Fuerza bruta / credential stuffing | Login automatizado | A6 | Media | Límite de tasa de Supabase Auth; **caché de sesiones de 60 s** para no consumirlo; el límite se traduce a HTTP 429 con mensaje explícito |
| T6 | Manipulación de la entrada | Payload malicioso | A1 | Alta | Validación estricta con Pydantic (tipos, rangos y campos obligatorios); consultas parametrizadas (PostgREST); SQL no se escribe a mano en la aplicación |
| T7 | Denegación de servicio | Ráfaga de peticiones | A1, A5 | Media | Validación de entrada (un payload inválido no llega al modelo); rate limiting del proveedor; carga medida y documentada |
| T8 | Abuso del modelo (decisión automática) | Uso indebido | A1 | Alta | El sistema **no** decide: la UI declara que es una estimación; el registro guarda quién realizó la evaluación; la política de privacidad lo hace explícito |
| T9 | Inyección de modelo (modelo envenenado) | `.joblib` manipulado | A5 | Alta | El artefacto se genera desde el notebook del repositorio; versiones de `scikit-learn`/`xgboost` **pinneadas** (un `.joblib` no es portable entre versiones); el preprocesado se verifica contra el pipeline original en los tests |
| T10 | Dependencia vulnerable | Paquete con CVE | A5 | Media | Versiones pinneadas; `pip install` sin caché; actualización planificada |
| T11 | Sesión no revocada | Token robado | A2 | Media | Expiración de 1 h en Supabase; cierre de sesión elimina el token del `localStorage`; el servidor valida `exp` en cada petición |
| T12 | Pérdida de trazabilidad | Decisión sin evidencia | A1 | Alta | Cada evaluación guarda `entradas`, `modelo_version`, `user_id` y marcas de tiempo |

---

## 4. Matriz de controles implementados

| # | Control | Implementación | Evidencia verificable |
|---|---|---|---|
| C1 | Aislamiento de datos por usuario | RLS: 4 políticas sobre `auth.uid() = user_id` | `scripts/verify_supabase.py` crea dos usuarios, comprueba que cada uno solo ve lo suyo y los elimina |
| C2 | Autenticación delegada | Supabase Auth (hash argon2 gestionado) | `POST /api/v1/auth/login` |
| C3 | Verificación de token en el servidor | PyJWT + JWKS cacheado; `exp`, `iat`, `aud`, `sub` | `api/core/security.py`; test de token inválido |
| C4 | Secretos fuera del repositorio | `.gitignore` con `.env`, `*.db`; `.env.example` sin valores | `git check-ignore -v .env` |
| C5 | Clave de servicio solo en servidor | Se usa en la API y en scripts de administración | El bundle del navegador no la contiene (verificado) |
| C6 | Validación de entrada | Pydantic: tipos, rangos, obligatorios, validadores de normalización | 8 tests de validación |
| C7 | CORS explícito | Lista de orígenes + regex para previsualizaciones de Vercel | Test de CORS (3 casos) |
| C8 | Contraseñas con hash | argon2-cffi (dashboard local heredado) | `src/database.py`; migración automática del registro antiguo |
| C9 | Mitigación de fuerza bruta | Caché de 60 s + HTTP 429 ante límite de tasa | `tests/test_sesion_cache.py` |
| C10 | Desfase de reloj tolerado | `leeway=300 s` | Desfase real medido: 4 min |
| C11 | Dependencias pinneadas | `requirements.txt` (desarrollo) y `requirements-api.txt` (producción) | Versiones exactas en los ficheros |
| C12 | Imagen mínima y endurecida | `python:3.11-slim`, usuario sin privilegios, `libgomp1` (XGBoost) | `Dockerfile` |
| C13 | Healthcheck y estado degradado | `/health` informa del estado del modelo y de Supabase | `render.yaml` (`healthCheckPath: /health`) |
| C14 | Cabeceras de seguridad en el frontend | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` | `frontend/vercel.json` |
| C15 | Privacidad desde el diseño | Política publicada, minimización de datos, sin decisiones automatizadas, sin cookies de terceros | Ruta `/privacidad` |
| C16 | Trazabilidad de cada evaluación | `entradas` (JSONB), `modelo_version`, `user_id`, `creado_en`, `actualizado_en` | `supabase/migrations/0001_init.sql` |

---

## 5. Gestión de secretos

| Secreto | Dónde se guarda | Rotación |
|---|---|---|
| `SUPABASE_SERVICE_ROLE_KEY` | Render → Environment (cifrado en reposo) | Cada vez que un miembro del equipo abandona el proyecto; **rotar si el `.env` se compartió** |
| `SUPABASE_ANON_KEY` | Render → Environment + bundle del navegador (es pública por diseño) | Con la service role |
| `TEST_USER_PASSWORD` | `.env` local (ignorado por git) | Antes de la entrega |
| Credenciales de Supabase CLI | `SUPABASE_ACCESS_TOKEN` en el entorno, nunca en el repo | Cada 90 días |

> La clave `anon` **está pensada para ser pública**: la seguridad no depende de ocultarla, sino de las políticas de RLS, que son la barrera real.

---

## 6. Requisitos de instalación y ejecución

### 6.1 Requisitos técnicos

| Elemento | Versión mínima | Verificación |
|---|---|---|
| Python | 3.11 | `python --version` |
| Node.js | 20 (22 recomendado) | `node -v` |
| Docker (opcional) | 24 | `docker -v` |
| k6 (opcional) | 0.50+ | `k6 version` |
| Proyecto Supabase | — | URL y claves en el panel |
| Navegador | Evergreen (Chrome, Edge, Firefox, Safari) | — |

### 6.2 Procedimiento de instalación (desarrollo)

```powershell
# 1. Dependencias
.\dropout-env\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
cd frontend; npm install; cd ..

# 2. Configuración
Copy-Item .env.example .env      # completar SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY

# 3. Esquema de la base de datos
.\dropout-env\Scripts\python.exe scripts\apply_migrations.py
.\dropout-env\Scripts\python.exe scripts\verify_supabase.py   # debe terminar en "verificada correctamente"

# 4. Modelo (si no existe)
.\dropout-env\Scripts\python.exe scripts\build_defaults.py

# 5. Usuario de acceso
.\dropout-env\Scripts\python.exe scripts\seed_user.py --email orientador@upn.edu.pe --password "..." --actualizar

# 6. Arranque
.\dropout-env\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000   # API
cd frontend; npm start                                                    # Frontend
```

### 6.3 Procedimiento de despliegue (producción)

Ver [`DEPLOY.md`](../DEPLOY.md). Resumen:

1. Backend en **Render** con el `Dockerfile` de la raíz (blueprint `render.yaml`).
2. Frontend en **Vercel** con *Root Directory* = `frontend` y variable `API_URL`.
3. `CORS_ORIGINS` en Render debe incluir el dominio exacto del frontend.
4. Healthcheck en `/health`; el despliegue debe reportar `"estado": "ok"`.

### 6.4 Verificación posterior a la instalación

```powershell
Invoke-RestMethod https://<api>/health                     # estado: ok
.\dropout-env\Scripts\python.exe -m pytest -q               # 71 tests
.\dropout-env\Scripts\python.exe scripts\verify_supabase.py # RLS y esquema
k6 run k6/smoke.js                                         # 0 errores
```

---

## 7. Plan de respuesta a incidentes

| Escenario | Detección | Respuesta | Comunicación |
|---|---|---|---|
| Clave filtrada | Revisión de commits / reporte | Rotar la clave en Supabase y en Render; invalidar tokens (`signOut` global) | Dirección de seguridad |
| Fuga de datos entre orientadores | Alerta de RLS / reporte de usuario | Suspender cuentas; revisar auditoría de `user_id`; evaluar notificación a los titulares | Dirección +affected |
| Token/JWT comprometido | Uso anómalo | Revocar la sesión del usuario en Supabase Auth | Equipo del proyecto |
| Vulnerabilidad en dependencia | Alerta de GitHub Dependabot | Actualizar la versión pinneada y reejecutar la suite | Equipo del proyecto |
| Caída de Supabase | `/health` en estado "degradado" | El modelo sigue respondiendo sin persistencia; activar plan de contingencia | Soporte técnico |

---

## 8. Pendientes de seguridad

| # | Acción | Prioridad |
|---|---|---|
| 1 | Rotar las claves de Supabase si el `.env` llegó a compartirse | **Alta** |
| 2 | Añadir la clave `anon` real a Render (hoy se usa la de servicio como respaldo) | **Alta** |
| 3 | Plan de hosting pago: instancia con recursos garantizados | Media |
| 4 | Política de contraseñas de los orientadores (longitud mínima, rotación) en Supabase Auth | Media |
| 5 | Copia de seguridad de la base de datos (hoy no hay copias propias) | Media |
| 6 | Registro de auditoría de accesos (quién consultó qué) | Baja |
| 7 | Pentesting externo antes de un uso institucionalextended | Baja |

---

## 9. Declaración de alcance responsable

EarlySign **no sustituye el criterio profesional del orientador** y no produce decisiones automatizadas con efectos jurídicos. La evaluación probabilistic apoya, no reemplaza. Esta distinción se comunica en la interfaz (nota bajo el panel), en la política de privacidad y en la documentación del modelo.

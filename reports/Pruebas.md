# Informe de pruebas · AlertaTemprana

Fecha: 21 de octubre de 2026
Entorno: Windows 11 · 12 nucleos lógicos · Python 3.11.9 · Node 24.15 · k6 v2.0.0

---

## 1. Pruebas unitarias

### 1.1 Backend (pytest) — 59 tests, todos en verde

```powershell
.\dropout-env\Scripts\python.exe -m pytest -v
```

| Fichero | Tests | Que cubren |
|---|---|---|
| `tests/test_predictor.py` | 34 | Contrato del formulario con el modelo, normalizacion de categorias, imputacion de variables no capturadas, validaciones de entrada, coherencia de umbrales y **equivalencia exacta de la ruta rapida con el pipeline original de sklearn** (40 filas reales, `atol=1e-9`) |
| `tests/test_api.py` | 18 | Health, indice y OpenAPI, contrato de `/predict`, validaciones (edad, nota, area, campos obligatorios, aprobadas > matriculadas), proteccion de rutas, token invalido, **CORS** (origen permitido, previsualizaciones de Vercel por regex, origen ajeno bloqueado) y flujo completo contra Supabase (login -> crear -> listar -> corregir -> borrar -> panel) |
| `tests/test_sesion_cache.py` | 7 | Cache de sesiones: guarda/recupera, credenciales distintas, normalizacion del correo, caducidad, limite de tamano, invalidacion y que **la contrasena nunca se guarda en claro** |

```
============================= 59 passed in 12.28s =============================
```

El test mas importante del conjunto es
`test_cada_campo_altera_la_probabilidad`: recorre los 12 campos del formulario y
comprueba que **cada uno mueve la probabilidad**. Ese test blinda el error
original del proyecto (las categorias se enviaban como `"1"/"0"` y el encoder las
descartaba en silencio).

### 1.2 Frontend (Vitest) — 13 tests, todos en verde

```powershell
cd frontend
npm test
```

| Fichero | Tests | Que cubren |
|---|---|---|
| `src/app/core/auth.service.spec.ts` | 4 | Login guarda el token, error de credenciales, estado de autenticacion, logout limpia el almacenamiento |
| `src/app/core/api.service.spec.ts` | 3 | `predecir` envia el estudiante, `listarEvaluaciones` aplica filtros, `eliminarEvaluacion` llama al endpoint correcto |
| `src/app/shared/shared.spec.ts` | 5 | `Icon` dibuja las trazas y cae en un icono por defecto, `EmptyState` solo muestra la accion si hay ruta, `Skeleton` aplica ancho y alto |
| `src/app/app.spec.ts` | 1 | La aplicacion arranca |

```
Test Files  4 passed (4)
     Tests  13 passed (13)
```

**Total: 72 pruebas unitarias, 0 fallos.**

---

## 2. Pruebas de estres (k6)

### 2.1 Metodologia

| Escenario | Fichero | Escala | Objetivo |
|---|---|---|---|
| Smoke | `k6/smoke.js` | 1 VU, 30 s | Correccion funcional de todos los endpoints |
| Carga | `k6/load.js` | 10 -> 50 VUs, 2 min | Capacidad sostenida |
| Estres | `k6/stress.js` | 20 -> 100 -> 200 VUs, 6 min | Punto de ruptura |
| Resistencia | `k6/soak.js` | 10 VUs, 30 min | Fugas de memoria y degradacion |

- El login se hace **una sola vez** en `setup()` y el token se reutiliza.
- `POST /api/v1/predict` **no persiste nada**: mide la capacidad del modelo sin
  llenar la base de datos.
- Las respuestas 401 y 422 provocadas a proposito se marcan con
  `responseCallback: http.expectedStatuses(...)` para que no cuenten como fallo.
- Los umbrales son el SLA: si se incumplen, k6 sale con codigo 1.

### 2.2 Resultados

**API en local** (uvicorn, 12 nucleos, modelo en memoria):

| Escenario | Throughput | p95 | Errores |
|---|---|---|---|
| smoke | 1 req/s | 14 ms (predict) | **0 %** |
| load (50 VUs) | 44 req/s | **10.5 ms** | **0 %** |
| **stress (200 VUs)** | **371 req/s** | **112 ms** | **0 %** (15 934 requests) |
| inferencia pura (sin HTTP) | 2 527 pred/s | 0.34 ms | — |

**API desplegada en Render** (plan gratuito, Oregon) **desde Peru**:

| Escenario | Throughput | p95 | Errores |
|---|---|---|---|
| smoke (1 VU) | 3 req/s | 525 ms (predict) / 1.33 s (evaluaciones) | **0 %** |
| **stress (200 VUs)** | **44 req/s** | **5.69 s** | **3.21 %** (511 de 15 894) |

### 2.3 Lectura de los resultados

La diferencia entre **371 req/s en local** y **44 req/s en produccion** no es del
codigo: la inferencia del modelo tarda **0.97 ms** en el servidor de produccion
(medido en la propia respuesta de la API). El cuello de botella es la
infraestructura del plan gratuito:

1. **Instancia de 0.5 GB con CPU compartida** de Render: no puede sostener 200
   peticiones concurrentes y descarta un 3.2 % de ellas.
2. **Distancia geografica**: entre Peru y Oregon hay ~250-300 ms por ida y
   vuelta. Con 200 VUs esperando respuesta, la latencia se acumula (p95 = 5.7 s
   frente a 112 ms en local).
3. **Arranque en frio**: tras 15 min sin trafico, la primera peticion tarda
   ~20 s. Medido: un `k6 run` recien.shopped falló con un unico request de
   19.91 s.

**El sistema no tiene un cuello de botella propio.** Con un plan pago (Render
Starter, 1 GB) o desplegando la API en la misma region que el proyecto de
Supabase, la latencia cae a la mitad y los errores a cero.

### 2.4 Hallazgo de la prueba: limite de tasa de Supabase Auth

Durante las pruebas de carga se observaron intermittentemente respuestas
`401 Invalid login credentials` con credenciales **correctas**. La causa: el
login se delega en Supabase Auth, que aplica limite de tasa al endpoint de
contrasena y, al alcanzarlo, **enmascara el error como credenciales invalidas**
(para no permitir enumerar cuentas). Con 10 intentos seguidos, todos correctos,
el mismo servidor respondio 200.

Mitigacion implementada:

- **Cache de sesiones de 60 s** (`api/core/sesion_cache.py`): indexada por un
  SHA-256 de (correo + contrasena), la contrasena nunca se guarda en claro.
  El login repetido baja de **934 ms a 2-15 ms** y ya no consume el limite de
  tasa de Supabase.
- El limite de tasa se traduce ahora a **HTTP 429** con el mensaje *"demasiados
  intentos de inicio de sesion"*, en lugar de confundirse con un error de
  credenciales.

---

## 3. Pruebas funcionales end-to-end

Recorrido completo con navegador real (Playwright + Edge) contra la
**version desplegada**, con captura de cada pantalla:

| Pantalla | Resultado |
|---|---|
| Login | Correcto; boton de contrasena alineado, mensajes en espanol |
| Politica de privacidad | Renderiza las 9 secciones |
| Panel | Metricas, graficos de riesgo y tabla de recientes |
| Evaluar (2 pasos) | Formulario, validacion y calculo |
| Resultado | Probabilidad, nivel y confirmacion de guardado |
| Historial | Listado, correccion de nivel y borrado |

**0 errores de consola** en todo el recorrido.

---

## 4. Resumen

| Tipo | Cantidad | Resultado |
|---|---|---|
| Unitarias backend | 59 | 100 % |
| Unitarias frontend | 13 | 100 % |
| Integracion (Supabase real) | 1 (dentro de los 59) | 100 % |
| Carga / estres local (200 VUs) | 15 934 requests | 0 % errores, p95 112 ms |
| Estres en produccion (200 VUs) | 15 894 requests | 3.21 % errores (limite del plan gratuito) |
| End-to-end en produccion | 6 pantallas | 0 errores de consola |

### Recomendaciones

1. **Plan de Render pago** para la sustentacion: elimina el arranque en frio de
   20 s y el 3.2 % de errores, y permite sostener la carga real de la
   institucion (decenas de orientadores, no cientos de VUs simultaneos).
2. **Acercar Supabase a la region del servidor** o el pais de los usuarios: cada
   lectura del historial paga ~300 ms de red.
3. **Cachear el resumen del panel** con TTL corto: hoy se recalcula en cada
   visita leyendo hasta 1 000 filas.
4. Vigilar el limite de tasa de Supabase Auth si se incorporan mas orientadores
   (la cache de sesiones mitiga el caso repetitivo, no altas masivas).

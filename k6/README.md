# Pruebas de carga con k6

k6 mide **rendimiento y estabilidad** del servicio. La correccion de la logica de negocio
se comprueba con `pytest` (backend) y `vitest` (frontend).

## Preparacion

```powershell
# 1. La API debe estar en marcha
.\dropout-env\Scripts\python.exe -m uvicorn api.main:app --port 8000

# 2. Variables de entorno
$env:BASE_URL      = "http://127.0.0.1:8000"
$env:TEST_EMAIL    = "orientador@alertatemprana.pe"
$env:TEST_PASSWORD = "..."
```

## Escenarios

| Script | Objetivo | Escala |
|---|---|---|
| `smoke.js` | Correctitud funcional: todos los endpoints responden | 1 VU, 30 s |
| `load.js` | Capacidad sostenida | 10 -> 50 VUs, 2 min |
| `stress.js` | Punto de ruptura | 20 -> 200 VUs, 6 min |
| `soak.js` | Fugas de memoria y degradacion | 10 VUs, 30 min |

```powershell
k6 run k6/smoke.js
k6 run k6/load.js
k6 run k6/stress.js
k6 run -e DURACION=30m k6/soak.js
```

## Como estan construidos

- El **login se hace una sola vez** en `setup()` y el token se reutiliza en todos los
  iteradores. En `soak.js` se renueva cada 10 minutos, porque el access token de Supabase
  caduca a la hora.
- `POST /api/v1/predict` **no persiste nada**: es el endpoint adecuado para medir la
  capacidad del modelo sin llenar la base de datos.
- Las respuestas 401 y 422 que se provocan a proposito se marcan con
  `responseCallback: http.expectedStatuses(...)` para que no cuenten como fallo.
- Los umbrales (`thresholds`) definen el SLA: si se incumplen, k6 sale con codigo 1.

## Resultados medidos (este equipo, 12 nucleos, API local)

| Escenario | p95 | Errores |
|---|---|---|
| `smoke` | 14 ms (predict) / 500 ms (evaluaciones) | 0 % |
| `load` (50 VUs) | **10.5 ms** | 0 % |
| Inferencia pura | 0.34 ms/prediccion (~2 500/s) | — |

**Donde se va el tiempo:** la inferencia del modelo es minima (~0.3 ms). Los endpoints que
leen de Supabase dependen de la latencia de red hacia el proyecto (~250-800 ms desde este
equipo). Si el cuello de botella es la base de datos, las palancas son:

1. Aplicar la migracion (indices + RLS) para que las consultas no_TIMEOUT.
2. Mover el resumen del panel a una vista SQL / RPC en vez de agregarlo en Python.
3. Cachear el resumen del panel con un TTL corto.
4. Desplegar la API en la misma region que el proyecto de Supabase.

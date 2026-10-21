# Plan de calidad · EarlySign

**Criterio de evaluación:** 3. Pruebas y control de calidad
**Versión:** 1.0 · 21 de octubre de 2026 · UPN

---

## 1. Objetivo del plan de calidad

Garantizar que EarlySign:

1. **Calcula correctamente** el nivel de riesgo a partir de los datos que introduce el orientador.
2. **No pierde ni mezcla** datos entre orientadores.
3. **Responde** dentro de un tiempo aceptable para un uso interactivo, incluso con carga.
4. **Es reproducible**: cualquiera puede reconstruir el modelo y el entorno desde el repositorio.
5. **Documenta** cada incidencia detectada, su análisis y su corrección.

---

## 2. Estrategia de pruebas

Pirámide de cuatro niveles, con la proporción de implementación actual:

```
            /\   E2E en producción            6 pantallas · 0 errores de consola
           /  \  Carga y estrés (k6)         200 VUs · 15 934 requests · 0 % errores (local)
          /    \ Integración                 1 flujo completo contra Supabase real
         /______\Unitarias                   59 pytest + 13 Vitest
```

| Nivel | Objetivo | Herramienta | Entorno | Frecuencia |
|---|---|---|---|---|
| **Unitario** | Lógica aislada de cada unidad | pytest · Vitest | Local | Cada commit |
| **Integración** | Interacción entre componentes y sistemas reales | pytest + `TestClient` | Local con red | Cada commit |
| **Sistema** | Recorrido completo de la aplicación | Playwright + Edge | Producción | Antes de cada entrega |
| **Carga / estrés** | Comportamiento bajo concurrencia | k6 | Local y producción | Antes de cada entrega |
| **Aceptación (UAT)** | Utilidad real para el orientador | ⟨instrumento: ver docs/EVALUACION_SOLUCION.md⟩ | UPN | Fin de T2 |

---

## 3. Alcance de las pruebas

### 3.1 N núcleo de inferencia (`src/predictor.py`) — 34 tests

| Área | Qué se verifica | Test representativo |
|---|---|---|
| Contrato de variables | El DataFrame tiene exactamente las 36 variables del modelo, en orden | `test_dataframe_tiene_las_mismas_variables_que_el_modelo` |
| Codificación de categorías | `"Sí"/"No"`, `"Masculino"/"Femenino"` se traducen a las etiquetas del encoder | `test_normalizacion_de_categoricas` |
| **Sensibilidad de cada campo** | **Los 12 campos del formulario cambian la probabilidad** | `test_cada_campo_altera_la_probabilidad` |
| Imputación | Las variables no capturadas toman la mediana del entrenamiento | `test_las_variables_no_capturadas_se_imputan_con_el_perfil_de_entrenamiento` |
| Validaciones | Edad 16-60, nota 0-20, aprobadas ≤ matriculadas, área conocida, booleano válido | `test_rechaza_*` (6 tests) |
| Salida | Probabilidad en [0,1] y nivel coherente con los umbrales | `test_probabilidad_en_rango_y_nivel_coherente` |
| **Equivalencia numérica** | La ruta rápida coincide con el pipeline de sklearn en 40 filas reales (`atol=1e-9`) | `test_la_ruta_rapida_coincide_con_el_pipeline_original` |

> El test de sensibilidad es el control crítico del proyecto: sin él, el defecto que se corrigió (6 de 13 variables descartadas en silencio) habría podido reintroducirse.

### 3.2 API (`api/`) — 18 tests

| Área | Qué se verifica |
|---|---|
| Sistema | `/health` responde con el modelo cargado; OpenAPI se genera |
| Contrato | `/predict` devuelve probabilidad, nivel y versión del modelo |
| Validación | Edad, nota, área y campos obligatorios se rechazan con 422 |
| Seguridad | Las rutas protegidas exigen token; un JWT inválido se rechaza con 401 |
| CORS | Origen permitido y previsualización de Vercel (regex) aceptados; origen ajeno bloqueado |
| Integración | Login real → crear → listar → corregir → borrar → panel, contra Supabase |

### 3.3 Caché de sesiones — 7 tests

Guardado/recuperación, credenciales distintas no comparten sesión, normalización del correo, caducidad, límite de tamaño, invalidación y **verificación de que la contraseña nunca se almacena en claro**.

### 3.4 Frontend (`frontend/`) — 13 tests

`AuthService` (login, error, estado, logout), `ApiService` (petición, filtros, borrado), componentes compartidos (`Icon`, `EmptyState`, `Skeleton`) y arranque de la aplicación.

### 3.5 Sistema (E2E) — 6 pantallas

Recorrido automatizado con navegador real contra la **versión desplegada**, con captura de cada pantalla y escucha de errores de consola:

| Pantalla | Verificación |
|---|---|
| Login | Autenticación correcta y mensaje de error ante credenciales inválidas |
| Privacidad | Renderizado de las 9 secciones sin autenticación |
| Panel | Carga de métricas, gráficos y tabla de recientes |
| Evaluar | Formulario de 2 pasos, validación y cálculo |
| Resultado | Probabilidad, nivel y confirmación de guardado |
| Historial | Listado, corrección de nivel y borrado |

**Resultado registrado:** 0 errores de consola en el recorrido completo.

### 3.6 Carga y estrés (k6)

| Escenario | Escala | Criterio de aceptación |
|---|---|---|
| `smoke.js` | 1 VU, 30 s | Todos los checks en verde, 0 % de errores |
| `load.js` | 10 → 50 VUs | p95 < 250 ms (local) / 1 500 ms (remoto), 0 % de errores |
| `stress.js` | 20 → 200 VUs | p95 < 1 500 ms, < 5 % de errores, 0 errores de validación |
| `soak.js` | 10 VUs, 30 min | p95 < 800 ms, sin degradación de throughput |

**Resultados registrados** (detalle en [`reports/Pruebas.md`](../reports/Pruebas.md)):

| Entorno | Throughput | p95 | Errores |
|---|---|---|---|
| Local | 371 req/s | 112 ms | 0 % |
| Producción (plan gratuito) | 44 req/s | 5,69 s | 3,21 % |

### 3.7 Fuera del alcance (declarado explícitamente)

- Pruebas de carga sobre la base de datos con miles de escrituras simultáneas (el diseño actual prioriza el endpoint de inferencia sin persistencia).
- Pruebas de seguridad ofensivas (pentesting) con terceros: fuera del alcance de un proyecto de tesis; se aplican controles defensivos documentados en el [plan de seguridad](PLAN_SEGURIDAD.md).
- Compatibilidad con navegadores heredados: se soporta evergreen (Chrome, Edge, Firefox, Safari actual).
- Pruebas de carga de la interfaz de usuario en dispositivos móviles: la aplicación es responsive, pero no se ha medido su rendimiento en condiciones de red móvil real.

---

## 4. Criterios de entrada y salida

### Entrada a una entrega

1. Todas las pruebas unitarias e integración en verde.
2. El build de producción compila sin errores ni advertencias.
3. La migración de base de datos (si aplica) es idempotente y se aplicó en un entorno de prueba.
4. El `k6 smoke` contra la API desplegada termina con 0 errores.

### Salida de una entrega

1. Todas las pruebas en verde en CI (GitHub Actions).
2. Recorrido E2E sin errores de consola en producción.
3. `k6 smoke` y `k6 load` con los umbrales de aceptación cumplidos.
4. Informe de pruebas actualizado (`reports/Pruebas.md`).
5. Registro de incidencias actualizado (§6).

---

## 5. Gestión de incidencias

Cada incidencia se registra con: descripción, pasos de reproducción, entorno, severidad, causa raíz, corrección y test de regresión que la previene.

| Severidad | Definición | Tiempo de respuesta | Requisito de salida |
|---|---|---|---|
| **Crítica** | Impide completar un proceso principal o expone datos | Inmediato | Bloquea la entrega |
| **Alta** | Función principal con errores; existeCircuito alternativo | 24 h | Bloquea la entrega |
| **Media** | Funcionalidad secundaria con error | 3 días | Se entrega con plan de corrección |
| **Baja** | Mejora de usabilidad o texto | 1 sprint | Backlog |

> Criterio de bloqueo: **toda incidencia crítica o alta debe quedar cerrada y cubierta por un test de regresión antes de entregar.**

---

## 6. Registro de incidencias detectadas y corregidas

Las 17 incidencias detectadas durante el desarrollo (y corregidas) están documentadas en el [README](../README.md §5). Las más relevantes para la calidad:

| # | Incidencia | Severidad | Causa raíz | Test de regresión |
|---|---|---|---|---|
| 1 | 6 de 13 variables del formulario no influían en la predicción | **Crítica** | Se enviaban `"1"/"0"` y códigos de carrera; el encoder con `handle_unknown="ignore"` las descartaba **sin error** | `test_cada_campo_altera_la_probabilidad` (12 casos) |
| 2 | 23 variables imputadas con `"0"` | Alta | Placeholder en lugar del perfil del entrenamiento | `test_las_variables_no_capturadas_se_imputan_con_el_perfil_de_entrenamiento` |
| 3 | La API no arrancaba con `CORS_ORIGINS` por comas | **Crítica** | `pydantic-settings` parseaba el campo como JSON | `test_cors_permite_los_origenes_configurados` |
| 4 | +300 ms por request | Alta | Se descargaba el JWKS en cada petición | Medido en el plan de rendimiento |
| 5 | Todos los tokens rechazados (401) | Alta | Desfase de 4 min entre el reloj local y Supabase | `leeway=300 s` |
| 6 | La API no arrancaba | Crítica | `supabase` 2.33.0 incompatible con su propio `ClientOptions` | `test_health` |
| 7 | 10,7 ms por predicción | Media | `sklearn` validando un DataFrame de 1 fila | `test_la_ruta_rapida_coincide_con_el_pipeline_original` |
| 8 | Contraseñas en texto plano | **Crítica** (seguridad) | Almacenamiento sin hash | `verificar_login` con argon2 |
| 9 | Las escrituras fallaban con RLS | Alta | La tabla no tenía `user_id` ni políticas | `scripts/verify_supabase.py` |
| 10 | Login bloqueado con credenciales correctas | Media | Límite de tasa de Supabase enmascarado como error de credenciales | `tests/test_sesion_cache.py` |
| 11 | Subtítulos de métricas recortados | Baja | Clase CSS duplicada con dos estilos | Verificación visual con capturas |
| 12 | Líneas de tabla desniveladas | Baja | Borde por celda en vez de por fila | Verificación visual con capturas |

---

## 7. Herramientas de apoyo

| Herramienta | Uso | Configuración |
|---|---|---|
| pytest | Tests backend | `pytest.ini` (marcadores, `testpaths`) |
| Vitest | Tests frontend | `frontend/angular.json` (builder `@angular/build:unit-test`) |
| k6 | Carga y estrés | `k6/config.js` (variables y generador de datos) |
| Playwright | E2E con navegador real | Script de captura (fuera del repo, en entorno de pruebas) |
| GitHub Actions | CI | `.github/workflows/ci.yml` (pytest → Vitest → build → k6 smoke) |
| SHAP | Interpretabilidad del modelo | `notebooks/02_modeling.ipynb` |
| Verificador de esquema | Comprobación de la migración | `scripts/verify_supabase.py` |

---

## 8. Mejora continua

| Periodo | Revisión |
|---|---|
| Cada entrega | Cobertura de pruebas, incidencias abiertas, cumplimiento de umbrales de k6 |
| Fin de T2 | Revisión con el asesor: suficiencia de la cobertura frente al riesgo de cada módulo |
| Fase siguiente (datos UPN) | Nuevo plan de validación del modelo con datos propios (ver [evaluación](EVALUACION_SOLUCION.md)) |

**Métrica de cobertura actual:** 100 % de los módulos de negocio con tests unitarios (núcleo de inferencia, API, caché, servicios de Angular). Los módulos de presentación (plantillas y estilos) se validan mediante el recorrido E2E con navegador real, que detecta además errores de consola.

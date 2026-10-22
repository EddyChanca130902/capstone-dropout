# Evaluación de la solución · EarlySign

**Criterio de evaluación:** 5. Indicadores y toma de datos
**Versión:** 1.0 · 21 de octubre de 2026 · UPN

Este documento define **cómo se va a medir si EarlySign sirve**. El plan ya está diseñado: el proyecto no termina en "funciona", sino que puede responder "funciona para quién, cuánto y cómo lo sabemos".

---

## 1. Justificación de la evaluación

El problema de partida era de **proceso**: la identificación de estudiantes en riesgo dependía del criterio individual y se producía tarde. Un sistema que acierta el 83 % de los abandonos, pero que el orientador no consulta o no le ahorra tiempo, **no resuelve el problema**.

Por eso la evaluación no se centra solo en el rendimiento del modelo, sino en tres dimensiones:

| Dimensión | Pregunta que responde | Fuente de datos |
|---|---|---|
| **Técnica** | ¿El modelo predice con exactitud suficiente? | Métricas sobre el test split + `reports/Pruebas.md` |
| **Operativa** | ¿El sistema se usa y ahorra tiempo? | Registros de la base de datos + hoja de uso |
| **Percibida** | ¿El orientador lo considera útil y confiable? | Cuestionario pre/post (Likert) |

---

## 1 bis. Los KPI como columna vertebral de la defensa

Un KPI suelto es un dato. Un KPI **anclado a una afirmación que el proyecto sostiene** es un argumento: es la evidencia que convence al jurado de que la afirmación es cierta.

Por eso cada indicador de este plan responde a una pregunta «¿qué afirma EarlySign y con qué lo demuestro?», y cada afirmación se sostiene en algún momento del guion de exposición.

### 1 bis.1 Mapa: afirmación → KPI → evidencia

| # | Afirmación que sostiene el software | KPI que la respalda | Evidencia verificable | Valor actual | Momento del guion |
|---|---|---|---|---|---|
| **A1** | **Detecta el abandono antes de que sea irreversible** | **KPI 1** cobertura de intervención · **KPI 2** variación del nivel de riesgo | Registro de derivaciones + reevaluación en el sistema | ⏳ pendiente de uso real | Parte 9 («Impacto») |
| **A2** | **La estimación es fiable, con sus límites declarados** | **I-T1** AUC · **I-T2** recall · **I-T6** Brier (calibración) | Test split 20 % estratificado + CV 5 folds | AUC **0.934** · recall **0.831** · Brier 0.092 | Parte 4 («El modelo») |
| **A3** | **No es una caja negra: el orientador sabe por qué** | **Coherencia con el juicio experto**: los 3 factores principales del modelo coinciden con los que el EDA identificó | `reports/figures/03_factores_binarios.png`, `04_notas_vs_dropout.png`, `06_shap_global_xgb.png` | Coincidencia de los 3 factores principales | Parte 4 |
| **A4** | **Resuelve el problema de gestión: prioriza y ahorra tiempo** | **KPI 4** tiempo de respuesta · **I-O5** tiempo de registro | Registro de derivaciones + cronómetro del formulario | ⏳ pendiente de uso real | Partes 1 y 9 |
| **A5** | **Es seguro con datos de estudiantes** | **I-O7** accesos a datos ajenos · **I-O8** disponibilidad | `scripts/verify_supabase.py` (2 usuarios reales) | **0 accesos ajenos** · 0 % de error en 15 934 requests | Parte 8 («Seguridad») |
| **A6** | **Cada decisión es auditable** | **I-O9** trazabilidad completa de la evaluación | SQL sobre `evaluaciones` (`entradas`, `modelo_version`, `user_id`, marcas de tiempo) | **100 %** de las filas | Parte 3 («Arquitectura») |
| **A7** | **Se puede mantener y reproducir** | **Cobertura de pruebas** por nível · **Integración en CI** | `reports/Pruebas.md`, `.github/workflows/ci.yml` | **72 tests** · CI en cada push | Parte 7 («Calidad») |
| **A8** | **Aguanta la carga real de la institución** | **I-T8** throughput · **I-T9** latencia p95 · **I-O6** latencia de la API | 4 escenarios de k6 (hasta 200 VUs) | **371 req/s** · p95 **112 ms** · 0 % de errores | Partes 3 y 7 |
| **A9** | **Es usable** en la consulta, no un trámite** | **I-O5** tiempo de registro · usabilidad (SUS, bloque 3 del cuestionario) | Cronómetro del formulario + cuestionario | ⏳ pendiente de uso real | Parte 6 («Demo») |

### 1 bis.2 Las objeciones previsibles y el KPI que las responde

Las preguntas del jurado ya son previsibles. Cada una tiene un KPI detrás que la resuelve:

| Objección probable del jurado | Respuesta | KPI que la sostiene |
|---|---|---|
| «¿Cómo sé que el modelo funciona y no es un invento?» | Test split estratificado con semilla fija, CV de 5 folds y comparación de 3 algoritmos | **I-T1, I-T2, I-T4** |
| «¿No estará sobreajustado?» | 20 % de test nunca visto en el entrenamiento + `modelo_version` en cada evaluación | **I-T1** + **I-O9** |
| «¿No será solo una caja negra?» | SHAP global y local: el panel muestra los factores queMotivan la alerta | **Coherencia con el EDA** (A3) |
| «¿Un orientador no podría hacerlo en un Excel?» | Tiempo de registro medido y ahorro declarado por los usuarios | **I-O5, I-E4** |
| «¿Cuántas alarmas falsas produce?» | Se miden sobre el desenlace real de cada caso | **KPI 2** (variación del riesgo) |
| «¿Y si un orientador ve datos de otro?» | Aislamiento en la base de datos, verificado con dos usuarios reales | **I-O7 = 0** |
| «¿Qué pasa si un estudiante señala de que está registrado?» | Minimización, RLS, trazabilidad y política pública; la decisión sigue siendo humana | **I-O9** + política de privacidad |
| ¿¿Aguanta si se conectan todos los orientadores?» | 371 req/s con 200 VUs y 0 % de errores | **I-T8, I-T9** |
| «¿Cómo se mantiene esto?» | 72 tests, integración contra Supabase real, E2E en producción y CI en cada push | **A7** |
| «¿Dónde está el modelo entrenado? ¿No es de la UPN» | Declarado como proxy en el informe, la interfaz y la política; hay un protocolo de validación con datos propios | **KPI 2 y KPI 3** (tras el piloto) |

### 1 bis.3 La regla que se sigue en la exposición

> **Ningún cifra se enuncia sin la afirmación que sostiene y la evidencia que la respalda.**
>
> No se dice «el AUC es 0,934»: se dice «la estimación es fiable, y lo sostengo con un AUC de 0,934 sobre un test del 20 % que el modelo nunca vió».
> No se dice «bingemos 371 peticiones por segundo»: se dice «la plataforma aguanta la carga de la institución, y lo sostengo con 371 req/s a 200 usuarios virtuales sin un solo error».

---

## 2. Indicadores

### 2.1 Indicadores técnicos del modelo (ya medidos)

| # | Indicador | Fórmula | Valor actual | Fuente |
|---|---|---|---|---|
| I-T1 | AUC-ROC | Área bajo la curva ROC sobre el test split | **0.934** | `notebooks/02_modeling.ipynb` |
| I-T2 | Recall sobre Dropout | TP / (TP + FN) | **0.831** | ídem |
| I-T3 | Precision sobre Dropout | TP / (TP + FP) | 0.806 | ídem |
| I-T4 | F1 | 2·(P·R)/(P+R) | **0.818** | ídem |
| I-T5 | PR-AUC | Área bajo la curva precisión-recall | 0.901 | ídem |
| I-T6 | Brier | Media de (predicción − resultado real)² | 0.092 | ídem |
| I-T7 | Tiempo de inferencia | Promedio de `tiempo_ms` en la respuesta de la API | **0.34 ms** (local) / 0.97 ms (producción) | respuestas de `/predict` |
| I-T8 | Throughput | Requests por segundo sostenidos | 371 req/s (local) | `k6` |
| I-T9 | Latencia p95 | Percentil 95 de la duración de la petición | 112 ms (local) | `k6` |

> **Interpretación honesta:** I-T1 a I-T6 miden el rendimiento **sobre la población de entrenamiento (Portugal)**. No son el rendimiento esperado en la UPN: ese se medirá con I-E1 (abajo). Presentarlos como si fueran el desempeño local sería una afirmación incorrecta.

### 2.2 Indicadores operativos del sistema

| # | Indicador | Fórmula | Meta | Fuente |
|---|---|---|---|---|
| I-O1 | Cobertura de evaluación | (Estudiantes con al menos 1 evaluación) / (Estudiantes matrícula activa) | ≥ 60 % en el primer semestre de uso | `evaluaciones` frente al padrón que reporte la UPN |
| I-O2 | Tasa de reevaluación | (Estudiantes con ≥ 2 evaluaciones) / (Estudiantes evaluados) | 20-35 % | `evaluaciones` |
| I-O3 | Casos en riesgo alto | COUNT(evaluaciones con nivel = 'ALTO' y es la última del DNI) | — (indicador de carga de trabajo) | Panel |
| I-O4 | Distribución por nivel | COUNT por nivel sobre la última evaluación de cada DNI | Distribución coherente con la capacidad de atención | Panel |
| I-O5 | Tiempo medio de registro | (hora de guardado − hora de envío) | < 3 min | `entradas` vs `creado_en` (con la marca temporal del formulario) |
| I-O6 | Tiempo de respuesta de la API | p95 de `http_req_duration` | < 250 ms (local) / < 1 500 ms (remoto) | `k6` |
| I-O7 | Incidencias de seguridad | Nº de accesos a datos ajenos detectados | **0** | `verify_supabase.py` + auditoría de RLS |
| I-O8 | Disponibilidad | (Requests con error 5xx) / (requests totales) | < 0,5 % | Logs de Render |
| **I-O9** | **Trazabilidad de la evaluación** | (Filas con `entradas` + `modelo_version` + `user_id` + marcas de tiempo completos) / (filas totales) | **100 %** | SQL sobre `evaluaciones` |

### 2.3 Indicadores de resultado: los 4 KPI de impacto (definidos por el autor)

Estos son los indicadores que miden si EarlySign **resuelve el problema**: no el rendimiento del
modelo, sino el efecto real del acompañamiento. Los cuatro se calculan **desde los datos del
sistema** (`GET /api/v1/kpis/impacto`), no de forma manual.

#### KPI 1 · Tasa de cobertura de intervención

```
(Estudiantes derivados a Acompanañamiento / Total de estudiantes detectados
 con alto nivel de riesgo) x 100
```

> *El modelo predictivo detecta el problema (riesgo de abandono asociado a la variable
> dependiente). Este KPI mide qué porcentaje de esos alumnos identificados reciben
> realmente una solución o plan de apoyo por parte del orientador académico.*

- **Fuente**: `evaluaciones` (nivel `ALTO` de la última evaluación de cada DNI) ∩ `intervenciones`.
- **Implementado en**: `api/services/kpis.py` → `kpi_cobertura_intervencion`.
- **Endpoint**: `GET /api/v1/kpis/impacto`.

#### KPI 2 · Tasa de variación del nivel de riesgo

```
(Estudiantes que disminuyeron su nivel de riesgo en una segunda evaluación /
 Total de estudiantes en riesgo que recibieron Acompanañamiento) x 100
```

> *Evalúa el impacto directo de la solución. Después de que el estudiante recibe la
> intervención, el orientador vuelve a correr el modelo en el sistema. Este KPI mide si la
> variable dependiente (nivel de riesgo) efectivamente bajó tras aplicar la solución.*

- Se compara el **nivel ordinal** (`BAJO` < `MEDIO` < `ALTO`) de la primera y de la última
  evaluación de cada estudiante con intervención.
- El informe incluye además la **disminución media de la probabilidad** como detalle.
- **Implementado en**: `kpi_reduccion_riesgo`.

#### KPI 3 · Índice de resolución de variables modificables

```
(Variables independientes académicas/psicosociales mejoradas post-intervención /
 Total de variables en alerta inicial) x 100
```

> *Se enfoca estrictamente en las variables independientes que la universidad puede ayudar a
> cambiar. Mide si las acciones correctivas lograron neutralizar los factores específicos
> que el sistema marcó como problemáticos.*

Variables que entran en el denominador (y su regla de mejora):

| Variable del modelo | Campo del formulario | Mejora cuando |
|---|---|---|
| `Curricular units 1st sem (approved)` | `cu1_aprobadas` | sube |
| `Curricular units 1st sem (grade)` | `cu1_nota` | sube |
| `Curricular units 2nd sem (approved)` | `cu2_aprobadas` | sube |
| `Curricular units 2nd sem (grade)` | `cu2_nota` | sube |
| `Tuition fees up to date` | `matricula_al_dia` | pasa de `No` a `Sí` |
| `Debtor` | `deudor` | pasa de `Sí` a `No` |

> Quedan **fuera** las variables no modificables por la institución (edad, género, área,
> desplazado, beca): no son objeto de ninguna acción correctiva, por lo que no pueden formar
> parte del denominador.

- Las "variables en alerta" de la evaluación inicial se obtienen de la **explicabilidad del
  modelo** (contribuciones SHAP): se guardan en `evaluaciones.factores_clave` al crear la
  evaluación.
- **Implementado en**: `kpi_resolucion_variables`.

#### KPI 4 · Tiempo de respuesta para Acompanañamiento

```
Sumatoria (Fecha de inicio de intervención - Fecha de evaluación en el sistema) /
Total de casos en riesgo
```

> *El sistema busca una identificación temprana. Este KPI mide la agilidad operativa:
> cuántos días pasan desde que el sistema diagnostica el problema (predicción) hasta que
> el responsable académico aplica la solución.*

- Se expresa en **días** (valor medio).
- **Implementado en**: `kpi_tiempo_respuesta`.

#### ¿Cómo se alimentan los KPI?

```
Formulario de evaluación
   → POST /api/v1/evaluaciones   (guarda entradas + factores en alerta)
        → GET  /api/v1/kpis/impacto  (calcula los 4 KPI al vuelo)
             → Vista /impacto  (4 tarjetas + registro de derivaciones)
```

Para que los KPI tengan datos hacen falta dos acciones del orientador:
1. **Evaluar** al estudiante (el sistema guarda la evaluación y sus variables en alerta).
2. **Registrar la derivación** a Acompanañamiento (con la fecha de inicio de la acción).

---

## 3. Instrumentos de toma de datos

### 3.1 Instrumento A — Cuestionario pre/post (orientadores)

**Momento:** antes de la primera uso (T0) y al cierre del periodo de evaluación (T1), con 30-45 días de uso en medio.
**Sujetos:** todos los orientadores que participan (muestra pequeña: 3-6 personas). Al ser una muestra pequeña, se reporta la distribución individual de respuestas, no solo el promedio.
**Escala:** Likert de 5 puntos (1 = totalmente en desacuerdo … 5 = totalmente de acuerdo).

**Bloque 1 — Necesidad y proceso actual (solo T0)**

| Ítem | Tipo |
|---|---|
| 1. En una semana típica, ¿cuántos estudiantes evalúo? | numérica |
| 2. ¿Cuánto tiempo dedico, en promedio, a evaluar a un estudiante? (min) | numérica |
| 3. ¿Cómo identifico hoy a los estudiantes en riesgo? (opción múltiple) | lista |
| 4. ¿Suelo perder de vista a un estudiante que necesitaba acompañamiento? | Likert |
| 5. ¿La priorización de casos depende de la disponibilidad de tiempo? | Likert |

**Bloque 2 — Percepción de utilidad (T1)**

| Ítem | Tipo |
|---|---|
| 6. EarlySign me ayuda a identificar estudiantes en riesgo que no había detectado | Likert |
| 7. El nivel de riesgo presentado es coherente con lo que yo observo en el estudiante | Likert |
| 8. La interfaz es fácil de usar | Likert |
| 9. El tiempo que ahorro con EarlySign es significativo | Likert |
| 10. Recomendaría EarlySign a otro orientador | Likert |
| 11. La priorización que propone el sistema me ayuda a decidir por quién empezar | Likert |
| 12. Confío en la predicción que muestra el sistema | Likert |
| 13. ¿Qué funcionalidades usarías con más frecuencia? (opción múltiple) | lista |

**Bloque 3 — SUS (System Usability Scale, 10 ítems) (T1)**

Escala de 5 puntos. Ítems originales de Brooke (1986) con puntuación: ítems impares positivos (puntuación = x − 1) e ítems pares negativos (puntuación = 5 − x). Resultado = (Σ / 50) × 100.

**Bloque 4 — Retroalimentación abierta (T1)**

- ¿Qué es lo que más te sirvió?
- ¿Qué es lo que menos te sirvió o te confundió?
- ¿Qué cambiarías?

> **Validity:** el instrumento combina escala Likert estructurada (comparables entre orientadores) con la escala SUS validada en la literatura, y se acompaña de preguntas numéricas de proceso que se contrastan con los registros objetivos del sistema (I-O5). Esto permite triangular: lo que el orientador *dice* que le ahorra tiempo con lo que el sistema *registra* que tarda.

### 3.2 Instrumento B — Hoja de registro de uso (sistema)

Se extrae automáticamente de la base de datos (no requiere trabajo adicional del orientador):

```sql
-- Casos evaluados, reevaluaciones y distribución de riesgo por semana
SELECT date_trunc('week', creado_en) AS semana,
       COUNT(DISTINCT dni)                                    AS estudiantes,
       COUNT(*)                                               AS evaluaciones,
       COUNT(*) FILTER (WHERE nivel = 'ALTO')                  AS riesgo_alto,
       ROUND(AVG(probabilidad)::numeric, 3)                   AS prob_media
  FROM evaluaciones
 WHERE user_id = :orientador
 GROUP BY 1 ORDER BY 1;
```

### 3.3 Instrumento C — Ficha de seguimiento del caso (30-60 días)

Una ficha por cada estudiante marcado como **ALTO** o **MEDIO** por EarlySign:

| Campo | Tipo | Nota |
|---|---|---|
| DNI (seudonimizado) | texto | No se usan nombres en el instrumento de análisis |
| Fecha de la alerta | fecha | Del sistema |
| Probabilidad y nivel | numérico / texto | Del sistema |
| ¿El orientador contacted al estudiante? | sí/no + fecha | |
| Motivo principal de la derivación | opción múltiple | Dificultad académica, Situation económica, Orientación vocacional, otro |
| Desenlace a 30 y 60 días | opción múltiple | Continúa estudios / Abandono / Retraso / Desconocido |
| ¿La alerta fue útil? | Likert 1-5 | |
| Observaciones | texto | |

**Cálculo de I-E1, I-E2 e I-E3** a partir de esta ficha.

```sql
-- I-O9: trazabilidad completa (debe dar 100 %)
SELECT COUNT(*) AS total,
       COUNT(*) FILTER (WHERE entradas IS NOT NULL
                          AND modelo_version IS NOT NULL
                          AND user_id IS NOT NULL
                          AND creado_en IS NOT NULL
                          AND actualizado_en IS NOT NULL) AS trazables,
       ROUND(100.0 * COUNT(*) FILTER (WHERE entradas IS NOT NULL
                          AND modelo_version IS NOT NULL
                          AND user_id IS NOT NULL) / NULLIF(COUNT(*), 0), 1) AS pct_trazable
  FROM evaluaciones;
```

### 3.4 Instrumento D — Validación con datos propios (fase siguiente)

Si la UPN puede facilitar el padrón y los historiales:

1. **Extracción** del padrón de matrícula y de los expedientes de ⟨2-3 cohortes⟩ (con las autorizaciones institucionales y la anonimización de los identificadores antes del análisis).
2. **Reconstrucción del dataset** con las 36 variables del modelo (las no disponibles se declaran como ausentes, no se inventan).
3. **Reentrenamiento y evaluación** con el mismo protocolo (mismo split, mismas métricas).
4. **Comparación** de AUC-ROC, recall y calibración entre el modelo de Portugal y el modelo propio.
5. **Decisión de despliegue** documentada: si el modelo propio supera al proxy, se migra el producto; si no, se mantiene el proxy con el umbral recalibrado.

> Este es el paso que convierte EarlySign de una demostración con un proxy en un sistema propio de la UPN. Requiere un acuerdo institucional de acceso a datos y, por tanto, queda fuera del alcance de T2.

---

## 4. Trazabilidad de los datos

Cada evaluación registrada permite reconstruir **cómo** se produjo el resultado:

| Campo | Origen | Permite reconstruir |
|---|---|---|
| `entradas` (JSONB) | Formulario del orientador | Los 13 datos tal como se introdujeron |
| `modelo_version` | `src/predictor.py` | Con qué versión del modelo se calculó |
| `probabilidad`, `nivel` | Salida del modelo | Qué se capturó de entrada y qué se devolvió |
| `user_id` | Supabase Auth | Quién realizó la evaluación |
| `creado_en`, `actualizado_en` | Postgres | Cuándo se registró y se corrigió |

Cadena de trazabilidad completa:

```
Ficha de seguimiento (C)  ←→  fila en `evaluaciones`  ←→  fila de `evaluaciones`
   (caso y desenlace)          (alerta emitida)            (entradas + modelo)
                                    │                            │
                                    └──── user_id ───────────────┘
```

El `user_id` permite además medir I-O2 y I-O3 por orientador, y auditar qué decisiones tomó cada persona.

---

## 5. Cómo se evaluará la solución

### 5.1 Diseño de la evaluación

| Fase | Momento | Actividad | Producto |
|---|---|---|---|
| **E0 · Línea base** | Antes del primer uso | Cuestionario A bloque 1; consulta al orientador sobre el proceso actual | Línea base de I-E4 y del proceso manual |
| **E1 · Piloto** | Semanas 1-2 | 3-5 orientadores evalúan con EarlySign; soporte presencial | Corrección de fricciones de uso |
| **E2 · Uso ordinario** | Semanas 3-8 | Uso ordinario; el sistema registra todo | I-O1 a I-O8 |
| **E3 · Cierre** | Semana 9 | Cuestionario A bloques 2 y 3 (T1); cierre de fichas de seguimiento | I-E1 a I-E8 |
| **E4 · Análisis** | Semana 10 | Triangulación de cuestionario, registros y fichas | Informe de evaluación |

### 5.2 Triangulación de fuentes

Cada afirmación de utilidad se contrasta con **al menos dos** fuentes independientes:

| Afirmación | Fuente 1 | Fuente 2 |
|---|---|---|
| "Ahorra tiempo" | Cuestionario (I-E4) | Registro del sistema (I-O5) |
| "Detecta casos que no se veían" | Cuestionario (ítem 6) | Ficha de seguimiento (I-E1) |
| "La predicción es correcta" | Cuestionario (ítem 7) | Ficha de seguimiento (I-E2, I-E3) |
| "Es fácil de usar" | SUS (I-E7) | Registro de uso y errores de las pruebas E2E |
| "El sistema es seguro" | Revisión técnica del plan de seguridad | `verify_supabase.py` (I-O7) |

### 5.3 Criterios de decisión

| Resultado | Interpretación | Acción |
|---|---|---|
| I-E5 ≥ 4,0 y I-E1 ≥ 50 % | La solución es útil y detecta temprano | **Escalar** a toda la unidad de orientación |
| I-E5 ≥ 4,0 pero I-E1 < 30 % | Se percibe útil, pero la cobertura es baja | Reforzar el uso (formación) o revisar el flujo |
| I-E5 < 3,0 | Baja utilidad percibida | **Revisar el diseño** con el asesor antes de escalar |
| I-E3 > 50 % | Demasiados falsos positivos | **Recalibrar umbrales** con los datos del piloto |
| I-E2 < 40 % | La predicción no se sostiene localmente | Revisar el modelo (variables, mapeo, dataset) |

### 5.4 Limitaciones del diseño de evaluación

1. **Muestra pequeña de orientadores** (3-6): no se pueden inferir generalizaciones estadísticas; se reportan las respuestas individuales y se usa el piloto como evaluación de usabilidad cualitativa.
2. **Periodo corto** (8 semanas): no hay tiempo suficiente para observar abandonios completos; por eso I-E1 se mide sobre el momento de la derivación, no sobre el desenlace final.
3. **El dataset de entrenamiento es externo**: I-E1 e I-E2 miden el desempeño *en uso*, que es la única medida que refleja el desempeño real de EarlySign; el AUC del modelo de Portugal no se extrapola.
4. **Sesgo de confirmación**: los orientadores que estarían dispuestos a usar el sistema pueden evaluar mejor su utilidad. Se mitiga con la pregunta explícita "¿cuántos evalúo por semana?" (E0) para detectar uso irregular.

---

## 6. Resumen de la evidencia disponible hoy

| Indicador | Estado | Verificado |
|---|---|---|
| I-T1 a I-T9 | ✅ Medidos | `reports/Pruebas.md`, `notebooks/02_modeling.ipynb` |
| I-O6, I-O8 | ✅ Medidos | `k6` contra la API desplegada |
| I-O7 | ✅ Verificado | `scripts/verify_supabase.py` |
| I-O1 a I-O6, I-O8, I-O9 | ⏳ En producción | Se extraerán del uso real y de la base de datos |
| **KPI 1** cobertura de intervención | ⏳ Pendiente de uso real | Se calcula solo: `GET /api/v1/kpis/impacto` |
| **KPI 2** variación del nivel de riesgo | ⏳ Pendiente de uso real | Se calcula solo: reevaluación tras la intervención |
| **KPI 3** resolución de variables modificables | ⏳ Pendiente de uso real | Se calcula solo: explicabilidad del modelo + segunda evaluación |
| **KPI 4** tiempo de respuesta | ⏳ Pendiente de uso real | Se calcula solo: fechas de derivación e inicio |

> **Lo que este documento añade al proyecto:** hasta ahora se había demostrado que el software *funciona* y que el modelo *predice*. Con este plan, el proyecto podrá demostrar además que EarlySign *resuelve el problema* para las personas que lo usan, con datos trazables y criterios de decisión explícitos.

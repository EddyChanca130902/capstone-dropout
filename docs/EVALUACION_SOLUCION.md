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

### 2.3 Indicadores de resultado (los que responde el problema)

| # | Indicador | Fórmula | Meta | Instrumento |
|---|---|---|---|---|
| **I-E1** | **Detección temprana** | (Estudiantes detectados por EarlySign antes de solicitar acompañamiento) / (Total de estudiantes quehasilan acompañamiento) | **≥ 50 %** del total de casos, frente a la detección reactiva actual | Ficha de seguimiento (§3.3) |
| **I-E2** | **Aciertos de la alerta** | (Casos marcados como ALTO que acabado abandonando) / (Casos marcados como ALTO) | ≥ 60 % (con el proxy; la validación local se ajustará) | Ficha de seguimiento |
| **I-E3** | **Falsos positivos** | (Casos marcados como ALTO que NO abandonaron) / (Casos marcados como ALTO) | ≤ 40 % | Ficha de seguimiento |
| **I-E4** | **Ahorro de tiempo** | (Tiempo medio de la evaluación con EarlySign) vs (tiempo medio estimado sin el sistema) | Reducción ≥ 30 % | Cuestionario (§3.1) |
| **I-E5** | **Utilidad percibida** | Media de las respuestas 4-5 en escala Likert del bloque "utilidad" | ≥ 4,0 / 5 | Cuestionario (§3.1) |
| **I-E6** | **Confianza en la predicción** | Media de las respuestas 4-5 en el bloque "confianza" | ≥ 3,8 / 5 | Cuestionario (§3.1) |
| **I-E7** | **Usabilidad percibida** | Media del puntaje SUS (System Usability Scale, 10 ítems) | ≥ 72 / 100 | Cuestionario (§3.1) |
| **I-E8** | **Claridad de la priorización** | % de orientadores que dicen "la lista de riesgo me ayudó a decidir por quién empezar" | ≥ 75 % | Cuestionario (§3.1) |

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
| I-O1 a I-O5, I-O8 | ⏳ En producción | Se extraerán del uso real |
| I-E1 a I-E8 | ⏳ Pendiente de T0/T1 | Instrumentos listos en este documento |

> **Lo que este documento añade al proyecto:** hasta ahora se había demostrado que el software *funciona* y que el modelo *predice*. Con este plan, el proyecto podrá demostrar además que EarlySign *resuelve el problema* para las personas que lo usan, con datos trazables y criterios de decisión explícitos.

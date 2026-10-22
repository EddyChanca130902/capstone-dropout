# Figuras de pruebas · EarlySign

**Para la exposición del criterio 3 (Pruebas y control de calidad) y del criterio 6 (Exposición).**

Las cuatro figuras de esta carpeta se generan con datos reales de las pruebas, no con
cifras escritas a mano. Para regenerarlas:

```powershell
# 1. Pruebas de carga instrumentadas (serie temporal)
$env:BASE_URL = "http://127.0.0.1:8000"     # o la URL de produccion
k6 run --out csv=carga_local.csv k6/grafico.js
k6 run --out csv=carga_prod.csv  k6/grafico.js

# 2. Generar las figuras
.\dropout-env\Scripts\python.exe scripts\generar_figuras.py
```

Salida en `reports/figures/`.

---

## Figura 08 · Comportamiento bajo carga (API en local)

![Comportamiento bajo carga](figures/08_carga_tiempo.png)

**Qué demuestra:** que la API **mantiene el caudal mientras suben los usuarios
virtuales** (20 → 100 → 200 VUs) y que la latencia p95 crece de forma suave
(escala logarítmica: de 3 ms a ~200 ms).

**Qué decir (20 segundos):**

> *Esta es la misma prueba que luego mostré contra el despliegue real. En la línea
> continua, el caudal: sube de forma prácticamente lineal con los usuarios
> virtuales, con un pico de 663 peticiones por segundo. Abajo, la latencia p95 en
> escala logarítmica: pasa de 3 milisegundos a unos 200. No hay uncollapseo, que
> es justo lo que se busca en una prueba de estrés: que el sistema se degrade de
> forma controlada y no que se caiga.*

**Dato de apoyo:** en toda la corrida hubo **0 errores** en 59 002 peticiones.

---

## Figura 09 · Cobertura de pruebas por nivel y por módulo

![Cobertura de pruebas](figures/09_pruebas_cobertura.png)

**Qué demuestra:** que las pruebas cubren **los 5 niveles** (unitarias,
integración, E2E con navegador real, carga) y que **todos los módulos de
negocio** tienen cobertura (núcleo de inferencia 34, API 18, caché 7, frontend 13).

**Qué decir (15 segundos):**

> *La cobertura no es solo un número: son cinco niveles. Unitarias para la lógica
> de negocio, integración contra Supabase real, end-to-end con un navegador real
> sobre la versión desplegada, y carga con k6. Y por módulo: el núcleo de
> inferencia, que es donde está el riesgo, es el más cubierto.*

**Dato de apoyo:** el test que exige que **cada campo del formulario mueva la
probabilidad** es el que blinda el defecto que describí antes.

---

## Figura 10 · Local frente a producción

![Comparativa de entornos](figures/10_comparativa_entornos.png)

**Qué demuestra:** que la diferencia entre local y producción **no es del
software**. Es de la infraestructura: 0,5 GB de RAM, CPU compartida y ~250 ms de
red hasta Oregon.

**Qué decir (15 segundos):**

> *Comparo los dos entornos con el mismo escenario. En local: 663 peticiones por
> segundo y 112 milisegundos de latencia p95. En producción: 48 por segundo y
> 4,7 segundos. Pero el dato que hay que mirar es otro: **la inferencia del
> modelo en el servidor de producción tarda 0,97 milisegundos**. Si el código
> fuera el cuello de botella, ese número sería alto. Es bajo. Lo que tarda es la
> red y la instancia compartida del plan gratuito.*

---

## Figura 11 · La misma prueba, dos entornos (la figura clave)

![Carga comparada](figures/11_carga_comparada.png)

**Qué demuestra:** en una sola imagen, las dos curvas. La verde (local) sigue
subiendo; la naranja (producción) **se aplana** en ~65 peticiones por segundo
mientras la latencia se dispara a varios segundos. El software escala; la
infraestructura del plan gratuito se satura.

**Qué decir (25 segundos):**

> *Esta es la figura que mejor explica el proyecto. Arriba, el caudal: en local
> sigue subiendo hasta 663 peticiones por segundo. En producción se queda plana
> en 65. Abajo, la latencia: en local se mantiene en cientos de milisegundos;
> en producción crece hasta varios segundos.*
>
> *La lectura correcta es: **la curva naranja no mide mi software, mide la
> instancia compartida de 0,5 gigabytes del plan gratuito**. Por eso la
> recomendación que hago en el informe es un plan con recursos garantizados, y
> por eso el sistema está preparado para escalar: el modelo se carga una vez en
> memoria, no por petición.*

**Dato de apoyo:** 0 % de errores en 59 002 peticiones locales; en producción el
3,2 % de errores son peticiones descartadas por la instancia, no por la
aplicación.

---

## Cómo encadenarlas en la exposición (60 segundos en total)

```
1. "Estas son las pruebas de carga."                    → Figura 08
2. "Y esto es lo que cubren."                           → Figura 09
3. "Ahora, la comparación entre entornos."              → Figura 10
4. "Y esto es lo que quiero que retengan:"              → Figura 11  (la clave)
```

**Regla:** en la figura 11, tu dedo (o el cursor) debe señalar primero la línea
verde y después la naranja, y terminar en la leyenda. La frase de cierre es:

> *El software escala; el plan gratuito de la plataforma es el que se satura.*

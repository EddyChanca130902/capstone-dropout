/**
 * Prueba de carga: mide el comportamiento del endpoint de prediccion bajo
 * trafico creciente y sostenido.
 *
 *   k6 run -e BASE_URL=http://localhost:8000 k6/load.js
 *
 * Objetivo por defecto: p95 < 500 ms y menos del 1 % de errores con 50 VUs.
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { API, estudianteAleatorio, iniciarSesion } from './config.js';

export const options = {
  stages: [
    { duration: '30s', target: 10 }, // ramp up
    { duration: '1m', target: 50 }, // carga sostenida
    { duration: '30s', target: 0 }, // bajada
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<250', 'p(99)<800'],
    checks: ['rate>0.99'],
    'errores_validacion': ['count==0'],
  },
};

const erroresValidacion = new Counter('errores_validacion');
const latenciaPrediccion = new Trend('latencia_prediccion', true);
const tasaExito = new Rate('tasa_exito');

export function setup() {
  const token = iniciarSesion();
  return { token };
}

export default function (data) {
  const respuesta = http.post(
    `${API}/predict`,
    JSON.stringify(estudianteAleatorio(__VU)),
    {
      headers: {
        'Content-Type': 'application/json',
        ...(data.token ? { Authorization: `Bearer ${data.token}` } : {}),
      },
      tags: { endpoint: 'predict' },
    },
  );

  const ok = check(respuesta, {
    'status 200': (r) => r.status === 200,
    'nivel valido': (r) => ['BAJO', 'MEDIO', 'ALTO'].includes(r.json('nivel')),
  });
  tasaExito.add(ok);
  latenciaPrediccion.add(respuesta.timings.duration);

  if (respuesta.status === 422) {
    erroresValidacion.add(1);
  }
  if (respuesta.status !== 200 && respuesta.status !== 422) {
    console.error(`[k6] ${respuesta.status}: ${respuesta.body}`);
  }

  sleep(0.5);
}

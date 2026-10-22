/**
 * Escenario de carga instrumentado para generar las figuras de la tesis.
 *
 * Registra series de tiempo (CSV) para poder graficar el comportamiento del
 * sistema durante la subida de carga: peticiones por segundo y latencias por
 * percentil frente a los usuarios virtuales activos.
 *
 *   k6 run --out csv=carga.csv k6/grafico.js
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { API, estudianteAleatorio, iniciarSesion } from './config.js';

export const options = {
  stages: [
    { duration: '30s', target: 20 }, // calentamiento
    { duration: '60s', target: 100 }, // carga sostenida
    { duration: '60s', target: 200 }, // punto de estres
    { duration: '30s', target: 0 }, // bajada
  ],
  thresholds: {
    http_req_failed: ['rate<0.05'],
  },
  summaryTrendStats: ['avg', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

export function setup() {
  return { token: iniciarSesion() };
}

export default function (data) {
  const respuesta = http.post(`${API}/predict`, JSON.stringify(estudianteAleatorio(__VU)), {
    headers: {
      'Content-Type': 'application/json',
      ...(data.token ? { Authorization: `Bearer ${data.token}` } : {}),
    },
    tags: { endpoint: 'predict' },
  });
  check(respuesta, { 'status 200': (r) => r.status === 200 });
  sleep(0.2);
}

/**
 * Prueba de estres: encuentra el punto de ruptura de la API subiendo los
 * usuarios virtuales hasta que el SLA se incumple.
 *
 *   k6 run -e BASE_URL=http://localhost:8000 k6/stress.js
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { API, estudianteAleatorio, iniciarSesion } from './config.js';

export const options = {
  stages: [
    { duration: '1m', target: 20 },
    { duration: '2m', target: 100 },
    { duration: '2m', target: 200 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.05'],
    'http_req_duration{endpoint:predict}': ['p(95)<1500'],
    checks: ['rate>0.95'],
  },
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

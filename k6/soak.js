/**
 * Prueba de resistencia (soak): trafico bajo y constante durante horas para
 * detectar fugas de memoria o degradacion.
 *
 *   k6 run -e BASE_URL=http://localhost:8000 -e DURACION=30m k6/soak.js
 *
 * El token de Supabase caduca a la hora: por eso el script vuelve a iniciar
 * sesion cada 10 minutos.
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { API, estudianteAleatorio, iniciarSesion } from './config.js';

const DURACION = __ENV.DURACION || '30m';
const REFRESH_CADA = __ENV.REFRESH_CADA || '10m';

export const options = {
  stages: [{ duration: DURACION, target: 10 }],
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<800'],
    checks: ['rate>0.99'],
  },
};

let token = null;
let ultimoRefresh = 0;
const refreshingEveryMs = 10 * 60 * 1000;

export function setup() {
  token = iniciarSesion();
  ultimoRefresh = Date.now();
  return { token };
}

export default function () {
  if (Date.now() - ultimoRefresh > refreshingEveryMs) {
    token = iniciarSesion();
    ultimoRefresh = Date.now();
    if (!token) {
      console.error('[k6] No se pudo renovar el token; se continua sin autenticacion');
    }
  }

  const respuesta = http.post(`${API}/predict`, JSON.stringify(estudianteAleatorio(__VU)), {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    tags: { endpoint: 'predict' },
  });
  check(respuesta, { 'status 200': (r) => r.status === 200 });
  sleep(1);
}

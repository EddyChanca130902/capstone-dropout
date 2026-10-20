/**
 * Smoke test: verifica que el servicio y sus endpoints responden correctamente.
 * Un solo usuario virtual, 30 segundos.
 *
 *   k6 run k6/smoke.js
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { API, BASE_URL, estudianteAleatorio, iniciarSesion } from './config.js';

// Umbrales parametrizables: en local la API responde en ~3 ms; desplegada en
// otra region la latencia la domina la red (250-500 ms).
//   k6 run -e UMBRAL_PREDICT_MS=1500 -e UMBRAL_EVAL_MS=3000 k6/smoke.js
const UMBRAL_PREDICT_MS = Number(__ENV.UMBRAL_PREDICT_MS || 300);
const UMBRAL_EVAL_MS = Number(__ENV.UMBRAL_EVAL_MS || 2000);

export const options = {
  vus: 1,
  duration: '30s',
  thresholds: {
    http_req_failed: ['rate<0.05'],
    'http_req_duration{endpoint:predict}': [`p(95)<${UMBRAL_PREDICT_MS}`],
    'http_req_duration{endpoint:evaluaciones}': [`p(95)<${UMBRAL_EVAL_MS}`],
    checks: ['rate>0.95'],
  },
};

export function setup() {
  const token = iniciarSesion();
  if (__ENV.TEST_EMAIL && !token) {
    throw new Error('No se pudo iniciar sesion: revisa TEST_EMAIL / TEST_PASSWORD');
  }
  return { token };
}

export default function (data) {
  const cabeceras = {
    'Content-Type': 'application/json',
    ...(data.token ? { Authorization: `Bearer ${data.token}` } : {}),
  };

  // 1. Salud del servicio
  const salud = http.get(`${BASE_URL}/health`);
  check(salud, {
    'health 200': (r) => r.status === 200,
    'health modelo cargado': (r) => r.json('modelo')?.variables === 36,
  });

  // 2. Prediccion sin persistir
  const prediccion = http.post(
    `${API}/predict`,
    JSON.stringify(estudianteAleatorio()),
    { headers: cabeceras, tags: { endpoint: 'predict' } },
  );
  check(prediccion, {
    'predict 200': (r) => r.status === 200,
    'predict nivel valido': (r) => ['BAJO', 'MEDIO', 'ALTO'].includes(r.json('nivel')),
    'predict probabilidad en rango': (r) => {
      const p = r.json('probabilidad');
      return p >= 0 && p <= 1;
    },
  });

  // 3. Validacion: debe rechazar datos invalidos (422 esperado)
  const invalido = http.post(
    `${API}/predict`,
    JSON.stringify({ dni: '1', nombre: 'X', edad: 99 }),
    {
      headers: cabeceras,
      tags: { endpoint: 'predict' },
      responseCallback: http.expectedStatuses(422),
    },
  );
  check(invalido, { 'predict rechaza datos invalidos': (r) => r.status === 422 });

  // 4. Endpoints protegidos sin token -> 401 (esperado)
  const sinToken = http.get(`${API}/evaluaciones`, {
    tags: { endpoint: 'evaluaciones' },
    responseCallback: http.expectedStatuses(401),
  });
  check(sinToken, { 'evaluaciones exige token': (r) => r.status === 401 });

  // 5. Historial autenticado
  if (data.token) {
    const historial = http.get(`${API}/evaluaciones?limite=5`, {
      headers: cabeceras,
      tags: { endpoint: 'evaluaciones' },
    });
    check(historial, { 'historial 200': (r) => r.status === 200 });

    const panel = http.get(`${API}/dashboard/resumen`, {
      headers: cabeceras,
      tags: { endpoint: 'dashboard' },
    });
    check(panel, { 'panel 200': (r) => r.status === 200 });
  }

  sleep(1);
}

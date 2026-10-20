/**
 * Configuracion y datos compartidos por los escenarios de k6.
 *
 * Variables de entorno:
 *   BASE_URL      http://localhost:8000
 *   TEST_EMAIL    orientador@alertatemprana.pe
 *   TEST_PASSWORD ...
 */

import http from 'k6/http';

export const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
export const API = `${BASE_URL}/api/v1`;

export const AREAS = [
  'Ingeniería y Tecnología',
  'Ciencias de la Salud',
  'Ciencias Sociales y Humanidades',
  'Administración y Negocios',
  'Arte y Diseño',
];

export const SI = 'Sí';
export const NO = 'No';

/** Genera un estudiante plausible y aleatorio. */
export function estudianteAleatorio(indice = 0) {
  const matriculadas = 4 + Math.floor(Math.random() * 4);
  const aprobadas1 = Math.floor(Math.random() * (matriculadas + 1));
  const matriculadas2 = 4 + Math.floor(Math.random() * 4);
  const aprobadas2 = Math.floor(Math.random() * (matriculadas2 + 1));

  return {
    dni: `K6${Date.now()}${indice}`.slice(0, 18),
    nombre: `Estudiante Carga ${indice}`,
    edad: 17 + Math.floor(Math.random() * 10),
    genero: Math.random() > 0.5 ? 'Masculino' : 'Femenino',
    area_estudios: AREAS[Math.floor(Math.random() * AREAS.length)],
    becario: Math.random() > 0.7 ? SI : NO,
    deudor: Math.random() > 0.8 ? SI : NO,
    matricula_al_dia: Math.random() > 0.85 ? NO : SI,
    desplazado: Math.random() > 0.6 ? SI : NO,
    cu1_matriculadas: matriculadas,
    cu1_aprobadas: aprobadas1,
    cu1_nota: Math.round(Math.random() * 200) / 10,
    cu2_matriculadas: matriculadas2,
    cu2_aprobadas: aprobadas2,
    cu2_nota: Math.round(Math.random() * 200) / 10,
  };
}

/** Inicia sesion contra la API y devuelve el access token. */
export function iniciarSesion() {
  const email = __ENV.TEST_EMAIL;
  const password = __ENV.TEST_PASSWORD;
  if (!email || !password) {
    return null;
  }
  const respuesta = http.post(
    `${API}/auth/login`,
    JSON.stringify({ email, password }),
    { headers: { 'Content-Type': 'application/json' }, timeout: '20s' },
  );
  if (respuesta.status !== 200) {
    console.error(`[k6] Login fallido (${respuesta.status}): ${respuesta.body}`);
    return null;
  }
  return respuesta.json('access_token');
}

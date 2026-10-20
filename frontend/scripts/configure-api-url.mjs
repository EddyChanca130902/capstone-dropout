/**
 * Escribe la URL de la API en `src/environments/environment.ts` antes del build.
 *
 * En Vercel se define la variable de entorno `API_URL` en el panel del
 * proyecto; en local, si no existe, se usa la del `.env` o la de desarrollo.
 *
 *   API_URL=https://mi-api.onrender.com/api/v1 npm run build
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const aqui = dirname(fileURLToPath(import.meta.url));
const destino = resolve(aqui, '..', 'src', 'environments', 'environment.ts');

function leerDelEnv() {
  // .env en la raiz del frontend (opcional, para builds locales)
  try {
    const contenido = readFileSync(resolve(aqui, '..', '.env'), 'utf8');
    for (const linea of contenido.split('\n')) {
      const [clave, ...resto] = linea.split('=');
      if (clave && clave.trim() === 'API_URL') {
        return resto.join('=').trim().replace(/^["']|["']$/g, '');
      }
    }
  } catch {
    // no hay .env: se usa la variable de entorno
  }
  return null;
}

const apiUrl = (process.env.API_URL || leerDelEnv() || 'http://localhost:8000/api/v1').replace(
  /\/+$/,
  '',
);

const contenido = `export const environment = {
  production: true,
  apiUrl: '${apiUrl}',
};
`;

writeFileSync(destino, contenido, 'utf8');
console.log(`[build] API_URL configurada: ${apiUrl}`);

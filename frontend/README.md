# EarlySign · Frontend (Angular 22)

SPA del sistema de alerta temprana: login, panel de indicadores, formulario de
evaluación en dos pasos e historial de evaluaciones.

## Desarrollo

```bash
npm install
npm start          # http://localhost:4200 (apunta a http://localhost:8000/api/v1)
npm test           # pruebas unitarias (Vitest)
npm run build      # build de produccion
```

## Build con la URL de la API

```bash
API_URL=https://mi-api.onrender.com/api/v1 npm run build
```

El script `scripts/configure-api-url.mjs` escribe esa URL en
`src/environments/environment.ts` antes de compilar. En Vercel se define la
variable de entorno `API_URL` en el panel del proyecto.

> Ojo: `npm run build` reescribe `src/environments/environment.ts` con la URL
> configurada. Si haces un build local sin `API_URL`, ese archivo quedara
> apuntando a `http://localhost:8000/api/v1` y aparecera como modificado en
> git (es esperado: el build de Vercel hace lo mismo).

## Despliegue en Vercel

- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist/frontend/browser`
- **Variable de entorno**: `API_URL`

La configuración completa está en `vercel.json`. La documentación del proyecto
(instalación, API, pruebas y despliegue) está en el
[README de la raíz](../README.md).

# Guía de despliegue · AlertaTemprana

El sistema tiene dos piezas que se despliegan por separado:

| Pieza | Plataforma | Configuración en el repo |
|---|---|---|
| Frontend (Angular 22) | **Vercel** | `frontend/vercel.json` |
| API (FastAPI) | **Render** | `Dockerfile` + `render.yaml` |

> Vercel solo aloja el frontend. La API necesita un servidor con Docker
> (Render, Railway o Fly.io) porque carga el modelo `.joblib` en memoria.

---

## Paso 0 · Publicar el código

```powershell
.\scripts\publicar.ps1
```

(El remoto `origin` ya está configurado; si cambias de repositorio, edita la
variable `$UrlGitHub` del script.)

---

## Paso 1 · API en Render

1. **https://render.com** → *New* → **Blueprint** → selecciona el repositorio.
2. Render detecta `render.yaml` y crea el servicio `alertatemprana-api`
   usando el `Dockerfile` de la raíz. El healthcheck es `GET /health`.
3. Completa las variables de entorno (en el panel o en el prompt):

   | Variable | Valor | Obligatoria |
   |---|---|---|
   | `CORS_ORIGINS` | `https://TU-FRONTEND.vercel.app` | sí (la actualízalas al final) |
   | `SUPABASE_URL` | `https://vgbiebpezleyuwzisrjc.supabase.co` | sí |
   | `SUPABASE_ANON_KEY` | clave **anon** de Supabase → Settings → API | sí |
   | `SUPABASE_SERVICE_ROLE_KEY` | clave **service_role** (solo servidor) | sí |
   | `API_ENV` | `production` | ya viene en `render.yaml` |

4. *Create* → Render construye la imagen (~3 min) y publica en
   `https://alertatemprana-api.onrender.com`.

### Verificar

```powershell
Invoke-RestMethod https://alertatemprana-api.onrender.com/health
```

Esperado:

```json
{
  "estado": "ok",
  "modelo": { "modelo_version": "xgboost-portugal-2026-10", "variables": 36 },
  "supabase": { "estado": "ok", "tablas": ["evaluaciones", "profiles"] }
}
```

Si aparece `"estado": "degradado"`, revisa las variables de entorno de Supabase.

---

## Paso 2 · Frontend en Vercel

1. **https://vercel.com** → *Add New* → **Project** → importa el repositorio.
2. **Root Directory**: `frontend` ← *imprescindible*
3. Vercel lee `frontend/vercel.json`:
   - Build Command: `npm run build`
   - Output Directory: `dist/frontend/browser`
   - Install Command: `npm ci`
4. **Settings → Environment Variables** → añade:

   | Variable | Valor |
   |---|---|
   | `API_URL` | `https://alertatemprana-api.onrender.com/api/v1` |

5. *Deploy*.

> El build ejecuta `frontend/scripts/configure-api-url.mjs`, que escribe esa URL
> en `src/environments/environment.ts` antes de compilar. **No hay que tocar
> código** para cambiar de API.

---

## Paso 3 · Cerrar el círculo del CORS

Vercel ya te habrá dado la URL final (p. ej. `https://capstone-dropout.vercel.app`).

1. Vuelve a **Render** → tu servicio → *Environment*.
2. Actualiza `CORS_ORIGINS` con esa URL exacta (sin barra final):
   `CORS_ORIGINS=https://capstone-dropout.vercel.app`
3. Guarda → Render redespliega automáticamente.

Si esto falla, el navegador mostrará en consola
`blocked by CORS policy`. Es siempre este paso.

---

## Paso 4 · Prueba de aceptación

```powershell
# 1. La API responde
Invoke-RestMethod https://alertatemprana-api.onrender.com/health

# 2. Login y predicción contra la API desplegada
$api = "https://alertatemprana-api.onrender.com/api/v1"
$sesion = Invoke-RestMethod -Method Post -Uri "$api/auth/login" -ContentType "application/json" `
    -Body '{"email":"orientador@alertatemprana.pe","password":"TU-CLAVE"}'
$token = $sesion.access_token

Invoke-RestMethod -Method Post -Uri "$api/predict" -ContentType "application/json" -Headers @{
    Authorization = "Bearer $token"
} -Body '{
    "dni":"70123456","nombre":"Prueba","edad":19,"genero":"Femenino",
    "area_estudios":"Ciencias de la Salud","becario":"No","deudor":"No",
    "matricula_al_dia":"Sí","desplazado":"No",
    "cu1_matriculadas":6,"cu1_aprobadas":1,"cu1_nota":6.0,
    "cu2_matriculadas":6,"cu2_aprobadas":0,"cu2_nota":5.0}'

# 3. Carga contra la API desplegada
$env:BASE_URL = "https://alertatemprana-api.onrender.com"
$env:TEST_EMAIL = "orientador@alertatemprana.pe"
$env:TEST_PASSWORD = "TU-CLAVE"
k6 run k6/smoke.js
```

Ojo: el plan gratuito de Render **se duerme tras 15 min de inactividad**, así que
la primera petición tarda ~50 s (arranque en frío). Para una sustentación, deja
la API "despertada" unos minutos antes o usa un plan pago.

---

## Checklist antes de publicar

- [ ] `SUPABASE_ANON_KEY` es la clave **anon** real (no la de servicio)
- [ ] Claves de Supabase rotadas si el `.env` llegó a compartirse
- [ ] Contraseña del usuario de prueba cambiada
- [ ] `CORS_ORIGINS` con el dominio exacto del frontend
- [ ] `pytest -q` en verde y `k6 run k6/smoke.js` sin errores
- [ ] `README.md` actualizado con la URL pública de la demo

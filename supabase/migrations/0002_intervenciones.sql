-- =============================================================================
-- EarlySign · Intervenciones y explicabilidad (idempotente)
--   Supabase > SQL Editor > New query > Run
--   (o: python scripts/apply_migrations.py)
--
-- Anade el registro de intervenciones de acompanamiento (que el orientador
-- documenta al derivar a un estudiante) y la explicabilidad de cada
-- evaluacion (variables que el modelo marco en alerta).
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Factores en alerta de cada evaluacion (top de contribuciones del modelo)
-- -----------------------------------------------------------------------------
alter table public.evaluaciones
    add column if not exists factores_clave jsonb,
    add column if not exists variables_en_alerta jsonb;

comment on column public.evaluaciones.factores_clave is
    'Variables que el modelo marco en alerta (contribucion positiva) y su valor al evaluar.';

comment on column public.evaluaciones.variables_en_alerta is
    'Lista de nombres de variable en alerta (derivada de factores_clave).';

-- -----------------------------------------------------------------------------
-- 2. Intervenciones de acompanamiento
-- -----------------------------------------------------------------------------
create table if not exists public.intervenciones (
    id                  bigint generated always as identity primary key,
    user_id             uuid not null default auth.uid()
                            references auth.users (id) on delete cascade,
    dni                 text not null,
    nombre              text,
    evaluacion_id       bigint references public.evaluaciones (id) on delete set null,
    -- Momento en que el sistema detecto el riesgo (para el KPI 4).
    fecha_deteccion     timestamptz not null default now(),
    -- Momento en que el orientador derivo / inicio la accion.
    fecha_derivacion    timestamptz not null default now(),
    -- Momento en que se aplico la accion concreta.
    fecha_inicio        timestamptz,
    responsable         text,
    canal               text,   -- tutoria | orientacion | becateo | derivacion | otro
    accion              text,   -- descripcion de la accion Correctiva
    estado              text not null default 'DERIVADA'
                            check (estado in ('DERIVADA', 'EN_PROCESO', 'CERRADA')),
    -- Variables que el modelo marco en alerta en la evaluacion de origen.
    variables_en_alerta jsonb not null default '[]'::jsonb,
    resultado           text,   -- cierre de la intervencion
    creado_en           timestamptz not null default now(),
    actualizado_en      timestamptz not null default now()
);

comment on table public.intervenciones is
    'Registro de las intervenciones de acompanamiento: base de los KPI de impacto.';

create index if not exists idx_intervenciones_user_fecha
    on public.intervenciones (user_id, fecha_derivacion desc);
create index if not exists idx_intervenciones_dni
    on public.intervenciones (dni);
create index if not exists idx_intervenciones_estado
    on public.intervenciones (estado);

-- -----------------------------------------------------------------------------
-- 3. Sello de actualizacion
-- -----------------------------------------------------------------------------
create or replace function public.tocar_actualizado_en()
returns trigger
language plpgsql
as $$
begin
    new.actualizado_en = now();
    return new;
end;
$$;

drop trigger if exists trg_intervenciones_actualizado on public.intervenciones;
create trigger trg_intervenciones_actualizado
    before update on public.intervenciones
    for each row execute function public.tocar_actualizado_en();

-- -----------------------------------------------------------------------------
-- 4. Row Level Security: cada orientador solo ve sus propias intervenciones
-- -----------------------------------------------------------------------------
alter table public.intervenciones enable row level security;

drop policy if exists "leer_propias_intervenciones" on public.intervenciones;
create policy "leer_propias_intervenciones" on public.intervenciones
    for select using (auth.uid() = user_id);

drop policy if exists "crear_propias_intervenciones" on public.intervenciones;
create policy "crear_propias_intervenciones" on public.intervenciones
    for insert with check (auth.uid() = user_id);

drop policy if exists "editar_propias_intervenciones" on public.intervenciones;
create policy "editar_propias_intervenciones" on public.intervenciones
    for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "borrar_propias_intervenciones" on public.intervenciones;
create policy "borrar_propias_intervenciones" on public.intervenciones
    for delete using (auth.uid() = user_id);

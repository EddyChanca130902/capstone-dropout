-- =============================================================================
-- AlertaTemprana · Esquema inicial (idempotente)
-- Ejecutar en: Supabase > SQL Editor > New query > Run
--   (o con: python scripts/apply_migrations.py)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Perfil de cada usuario autenticado
-- -----------------------------------------------------------------------------
create table if not exists public.profiles (
    id          uuid primary key references auth.users (id) on delete cascade,
    nombre      text not null default 'Orientador',
    rol         text not null default 'orientador',
    creado_en   timestamptz not null default now()
);

comment on table public.profiles is 'Datos de perfil del orientador (1:1 con auth.users)';

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    insert into public.profiles (id, nombre)
    values (
        new.id,
        coalesce(new.raw_user_meta_data ->> 'nombre', split_part(new.email, '@', 1))
    )
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();

-- -----------------------------------------------------------------------------
-- 2. Evaluaciones: se amplía la tabla existente sin perder datos
-- -----------------------------------------------------------------------------
alter table public.evaluaciones
    add column if not exists user_id        uuid references auth.users (id) on delete cascade,
    add column if not exists modelo_version text,
    add column if not exists entradas       jsonb,
    add column if not exists creado_en      timestamptz default now(),
    add column if not exists actualizado_en timestamptz default now();

-- Backfill: las filas anteriores heredan la fecha de creacion original.
update public.evaluaciones
   set creado_en = coalesce(creado_en, created_at)
 where creado_en is null;

-- El autor se rellena solo si no viene en la peticion (la politica de RLS exige
-- que `user_id` coincida con `auth.uid()`).
alter table public.evaluaciones
    alter column user_id set default auth.uid();

-- -----------------------------------------------------------------------------
-- 3. Indices
-- -----------------------------------------------------------------------------
create index if not exists idx_evaluaciones_user_creado
    on public.evaluaciones (user_id, creado_en desc);
create index if not exists idx_evaluaciones_dni
    on public.evaluaciones (dni);
create index if not exists idx_evaluaciones_nivel
    on public.evaluaciones (nivel);

-- -----------------------------------------------------------------------------
-- 4. Row Level Security: cada orientador solo ve sus propias evaluaciones
-- -----------------------------------------------------------------------------
alter table public.profiles    enable row level security;
alter table public.evaluaciones enable row level security;

drop policy if exists "perfil_propio" on public.profiles;
create policy "perfil_propio" on public.profiles
    for select using (auth.uid() = id);

drop policy if exists "leer_propias" on public.evaluaciones;
create policy "leer_propias" on public.evaluaciones
    for select using (auth.uid() = user_id);

drop policy if exists "crear_propias" on public.evaluaciones;
create policy "crear_propias" on public.evaluaciones
    for insert with check (auth.uid() = user_id);

drop policy if exists "editar_propias" on public.evaluaciones;
create policy "editar_propias" on public.evaluaciones
    for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "borrar_propias" on public.evaluaciones;
create policy "borrar_propias" on public.evaluaciones
    for delete using (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- 5. Sello de actualizacion automatica
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

drop trigger if exists trg_evaluaciones_actualizado on public.evaluaciones;
create trigger trg_evaluaciones_actualizado
    before update on public.evaluaciones
    for each row execute function public.tocar_actualizado_en();

-- -----------------------------------------------------------------------------
-- 6. Vista de apoyo para el panel (opcional, la API tambien la calcula)
-- -----------------------------------------------------------------------------
create or replace view public.v_evaluaciones_recientes as
select id,
       dni,
       nombre,
       area_estudios,
       probabilidad,
       nivel,
       modelo_version,
       creado_en
  from public.evaluaciones;

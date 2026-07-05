-- =============================================================================
-- NichePulse — Esquema de Supabase
-- Corré esto en el SQL Editor de tu proyecto de Supabase (Database > SQL Editor)
-- =============================================================================

-- Extensión necesaria para generar UUIDs con gen_random_uuid()
create extension if not exists "pgcrypto";

-- -----------------------------------------------------------------------------
-- 1) niches — la tabla central. Acá vive todo lo que el home y la calculadora
--    leen para mostrarse (score, CPM, tendencia, categoría).
-- -----------------------------------------------------------------------------
create table if not exists niches (
  id              uuid primary key default gen_random_uuid(),
  name            text not null unique,
  category        text not null,
  search_volume   integer not null default 0,
  competition     text check (competition in ('baja', 'media', 'alta')) default 'media',
  avg_cpm         numeric(6,2) not null default 0,       -- usado por la calculadora de ingresos
  score           integer not null default 0,             -- 0-100, usado por el ranking del home
  trend_delta     numeric(5,2) not null default 0,        -- variación %, positiva o negativa
  trend_series    jsonb not null default '[]',            -- array de 8 números para el sparkline
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index if not exists idx_niches_category on niches (category);
create index if not exists idx_niches_score on niches (score desc);

-- -----------------------------------------------------------------------------
-- 2) youtube_channels — resultado de youtube_channel_collector.py
--    Cada canal opcionalmente pertenece a un nicho (para agregarlo a sus stats).
-- -----------------------------------------------------------------------------
create table if not exists youtube_channels (
  channel_id             text primary key,               -- el "UC..." de YouTube
  niche_id               uuid references niches(id) on delete set null,
  name                   text,
  subscribers            bigint not null default 0,
  total_views            bigint not null default 0,
  video_count            integer not null default 0,
  avg_views_last_videos  numeric(12,2) not null default 0,
  sampled_videos         integer not null default 0,
  fetched_at             timestamptz not null default now()
);

create index if not exists idx_channels_niche on youtube_channels (niche_id);

-- -----------------------------------------------------------------------------
-- 3) niche_content_suggestions — resultado de niche_content_ideas.py
--    Guardamos el JSON tal cual sale del modelo (video_ideas + faqs).
-- -----------------------------------------------------------------------------
create table if not exists niche_content_suggestions (
  id            uuid primary key default gen_random_uuid(),
  niche_id      uuid not null references niches(id) on delete cascade,
  video_ideas   jsonb not null,   -- [{ "title": "...", "angle": "..." }, ...] (5 items)
  faqs          jsonb not null,   -- [{ "question": "...", "answer": "..." }, ...] (3 items)
  generated_at  timestamptz not null default now()
);

create index if not exists idx_suggestions_niche on niche_content_suggestions (niche_id);

-- -----------------------------------------------------------------------------
-- updated_at automático en niches
-- -----------------------------------------------------------------------------
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_niches_updated_at on niches;
create trigger trg_niches_updated_at
  before update on niches
  for each row execute function set_updated_at();

-- -----------------------------------------------------------------------------
-- Row Level Security
-- La web (con la clave "anon") solo puede LEER. Escribir/actualizar queda
-- reservado a tus scripts, que usan la SERVICE_ROLE key (esa key ignora RLS,
-- así que no necesita policy propia).
-- -----------------------------------------------------------------------------
alter table niches enable row level security;
alter table youtube_channels enable row level security;
alter table niche_content_suggestions enable row level security;

create policy "Lectura pública de niches"
  on niches for select
  using (true);

create policy "Lectura pública de youtube_channels"
  on youtube_channels for select
  using (true);

create policy "Lectura pública de niche_content_suggestions"
  on niche_content_suggestions for select
  using (true);

-- -----------------------------------------------------------------------------
-- Datos de ejemplo (opcional) — para probar el home sin correr los scripts todavía
-- -----------------------------------------------------------------------------
insert into niches (name, category, search_volume, competition, avg_cpm, score, trend_delta, trend_series)
values
  ('Finanzas Personales', 'Dinero', 74000, 'media', 12.40, 94, 6.2, '[40,44,42,50,55,60,68,74]'),
  ('Fitness en Casa', 'Salud', 51000, 'alta', 5.80, 88, 3.1, '[50,52,48,55,58,60,63,66]'),
  ('Mascotas Exóticas', 'Animales', 22000, 'baja', 3.20, 81, -1.4, '[60,58,62,59,57,55,54,52]')
on conflict (name) do nothing;

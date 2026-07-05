import { createClient } from "@supabase/supabase-js";

// Cliente para usar en el navegador (componentes "use client").
// La ANON key es segura de exponer: las tablas tienen RLS que solo permite
// lectura pública (ver supabase_schema.sql), nunca escritura desde acá.
export const supabaseBrowser = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
);

// Cliente para usar en Server Components / route handlers (más rápido,
// sin round-trip extra, y podría usarse con la service key si algún día
// necesitás escribir desde el propio Next.js).
export function getSupabaseServerClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  );
}

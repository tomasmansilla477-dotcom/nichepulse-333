import { getSupabaseServerClient } from "@/lib/supabaseClient";
import NichePulseHomeClient from "@/components/NichePulseHomeClient";

// ISR: Next.js regenera esta página como máximo cada 1 hora (3600s).
// Esto es lo que hace que "la gente entre y vea los nichos actualizados"
// sin que vos tengas que redeployar nada — el propio Next.js vuelve a pedir
// los datos a Supabase automáticamente en segundo plano.
export const revalidate = 3600;

export default async function Page() {
  const supabase = getSupabaseServerClient();

  const { data: niches, error } = await supabase
    .from("niches")
    .select("name, category, score, trend_delta, trend_series")
    .order("score", { ascending: false });

  if (error) {
    console.error("Error trayendo niches de Supabase:", error.message);
  }

  return <NichePulseHomeClient niches={niches ?? []} />;
}

"use client";

import { useState, useMemo } from "react";
import { Search, ArrowUpRight, ArrowDownRight, Activity, Sparkles } from "lucide-react";

function Sparkline({ data, positive }) {
  if (!data || data.length === 0) return <div className="h-8" />;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  return (
    <div className="flex items-end gap-[3px] h-8">
      {data.map((v, i) => {
        const h = 6 + ((v - min) / range) * 26;
        return (
          <div
            key={i}
            style={{ height: `${h}px` }}
            className={`w-1 rounded-sm ${positive ? "bg-teal-500/70" : "bg-rose-500/70"}`}
          />
        );
      })}
    </div>
  );
}

// niches: [{ name, category, score, trend_delta, trend_series }, ...]
// viene del server component (app/page.jsx), que a su vez lo trae de Supabase.
export default function NichePulseHomeClient({ niches }) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("Todos");

  const categories = useMemo(
    () => ["Todos", ...Array.from(new Set(niches.map((n) => n.category)))],
    [niches]
  );

  const filtered = useMemo(() => {
    return niches.filter((n) => {
      const matchesQuery = n.name.toLowerCase().includes(query.toLowerCase());
      const matchesCategory = category === "Todos" || n.category === category;
      return matchesQuery && matchesCategory;
    });
  }, [niches, query, category]);

  return (
    <div className="min-h-screen w-full bg-zinc-950 text-zinc-100 antialiased">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');
        .font-display { font-family: 'Space Grotesk', sans-serif; }
        .font-body { font-family: 'Inter', sans-serif; }
        .font-mono-data { font-family: 'JetBrains Mono', monospace; }
        @keyframes pulseLine { 0%, 100% { stroke-dashoffset: 0; } 50% { stroke-dashoffset: 12; } }
        .pulse-path { stroke-dasharray: 6 6; animation: pulseLine 3.5s linear infinite; }
        @media (prefers-reduced-motion: reduce) { .pulse-path { animation: none; } }
      `}</style>

      <div className="font-body max-w-5xl mx-auto px-6 sm:px-8">
        <header className="flex items-center justify-between pt-8">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-amber-400" strokeWidth={2.5} />
            <span className="font-display font-semibold text-lg tracking-tight">NichePulse</span>
          </div>
          <nav className="hidden sm:flex items-center gap-6 text-sm text-zinc-400">
            <a href="#" className="hover:text-zinc-100 transition-colors">Nichos</a>
            <a href="#" className="hover:text-zinc-100 transition-colors">Precios</a>
            <a href="#" className="hover:text-zinc-100 transition-colors">Blog</a>
          </nav>
        </header>

        <section className="pt-16 sm:pt-20 pb-10">
          <div className="font-mono-data text-xs tracking-[0.2em] text-amber-400/90 uppercase mb-4">
            {niches.length} nichos · actualizado automáticamente
          </div>
          <h1 className="font-display text-4xl sm:text-5xl font-semibold leading-[1.1] tracking-tight max-w-2xl">
            Encontrá tu próximo nicho antes de que se sature.
          </h1>
          <p className="mt-4 text-zinc-400 max-w-xl leading-relaxed">
            Datos de demanda, competencia y tendencia actualizados todos los días.
            Buscá, comparás y decidís con números, no con intuición.
          </p>

          <div className="mt-8 max-w-xl">
            <div className="flex items-center gap-3 bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-3 focus-within:border-amber-400/60 transition-colors">
              <Search className="w-4 h-4 text-zinc-500 shrink-0" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Buscar un nicho — ej. finanzas, mascotas, fitness..."
                className="w-full bg-transparent outline-none text-sm placeholder:text-zinc-600"
              />
              <kbd className="hidden sm:inline-flex items-center justify-center text-[10px] font-mono-data text-zinc-500 border border-zinc-700 rounded px-1.5 py-0.5">/</kbd>
            </div>
          </div>
        </section>

        <div className="py-6" aria-hidden="true">
          <svg width="100%" height="24" viewBox="0 0 600 24" preserveAspectRatio="none" className="opacity-70">
            <path d="M0,12 L220,12 L235,2 L250,22 L265,12 L600,12" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-zinc-700 pulse-path" />
          </svg>
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-2 -mx-1 px-1 scrollbar-none">
          {categories.map((c) => (
            <button
              key={c}
              onClick={() => setCategory(c)}
              className={`shrink-0 text-sm px-3.5 py-1.5 rounded-full border transition-colors ${
                category === c
                  ? "bg-amber-400 text-zinc-950 border-amber-400 font-medium"
                  : "border-zinc-800 text-zinc-400 hover:text-zinc-100 hover:border-zinc-600"
              }`}
            >
              {c}
            </button>
          ))}
        </div>

        <section className="mt-6 mb-24 border border-zinc-800 rounded-xl overflow-hidden">
          <div className="hidden sm:grid grid-cols-[2.5rem_1fr_6rem_5.5rem_4rem] gap-4 px-5 py-3 text-[11px] uppercase tracking-wider text-zinc-500 font-mono-data border-b border-zinc-800 bg-zinc-900/40">
            <span>#</span>
            <span>Nicho</span>
            <span>Tendencia</span>
            <span className="text-right">Var.</span>
            <span className="text-right">Score</span>
          </div>

          {filtered.length === 0 && (
            <div className="px-5 py-10 text-center text-sm text-zinc-500">
              No encontramos ningún nicho para "{query}". Probá con otra búsqueda.
            </div>
          )}

          {filtered.map((n, i) => {
            const positive = n.trend_delta >= 0;
            return (
              <div
                key={n.name}
                className="grid grid-cols-[2.5rem_1fr_auto] sm:grid-cols-[2.5rem_1fr_6rem_5.5rem_4rem] gap-4 items-center px-5 py-4 border-b border-zinc-800/70 last:border-b-0 hover:bg-zinc-900/50 transition-colors group"
              >
                <span className="font-mono-data text-sm text-zinc-600 group-hover:text-amber-400 transition-colors">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div>
                  <div className="font-medium text-zinc-100">{n.name}</div>
                  <div className="text-xs text-zinc-500">{n.category}</div>
                </div>
                <div className="hidden sm:block">
                  <Sparkline data={n.trend_series} positive={positive} />
                </div>
                <div className={`hidden sm:flex items-center justify-end gap-1 text-sm font-mono-data ${positive ? "text-teal-400" : "text-rose-400"}`}>
                  {positive ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                  {Math.abs(n.trend_delta).toFixed(1)}%
                </div>
                <div className="text-right font-mono-data text-lg font-semibold text-zinc-100">{n.score}</div>
              </div>
            );
          })}
        </section>

        <footer className="pb-10 flex items-center justify-between text-xs text-zinc-600 border-t border-zinc-900 pt-6">
          <span className="flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" /> NichePulse — datos actualizados cada 24h
          </span>
          <span>© 2026</span>
        </footer>
      </div>
    </div>
  );
}

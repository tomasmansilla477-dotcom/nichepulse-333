"use client";

import { useState, useEffect, useMemo } from "react";
import { DollarSign, Eye, Loader2 } from "lucide-react";
import { supabaseBrowser } from "@/lib/supabaseClient";

const MIN_VIEWS = 10_000;
const MAX_VIEWS = 1_000_000;
const ratio = MAX_VIEWS / MIN_VIEWS;

function positionToViews(pos) {
  return Math.round(MIN_VIEWS * Math.pow(ratio, pos / 100));
}

export default function YoutubeEarningsCalculatorClient() {
  const [sliderPos, setSliderPos] = useState(50);
  const [niches, setNiches] = useState([]);
  const [selectedNiche, setSelectedNiche] = useState(null);
  const [loading, setLoading] = useState(true);

  // Trae la lista de nichos con su CPM real, una sola vez al montar.
  useEffect(() => {
    let cancelled = false;
    async function loadNiches() {
      setLoading(true);
      const { data, error } = await supabaseBrowser
        .from("niches")
        .select("name, avg_cpm")
        .order("name", { ascending: true });

      if (!cancelled) {
        if (error) {
          console.error("Error trayendo CPM de Supabase:", error.message);
        } else if (data && data.length > 0) {
          setNiches(data);
          setSelectedNiche(data[0].name);
        }
        setLoading(false);
      }
    }
    loadNiches();
    return () => {
      cancelled = true;
    };
  }, []);

  const monthlyViews = useMemo(() => positionToViews(sliderPos), [sliderPos]);
  const cpm = niches.find((n) => n.name === selectedNiche)?.avg_cpm ?? 0;
  const monthlyEarnings = (monthlyViews / 1000) * cpm;
  const yearlyEarnings = monthlyEarnings * 12;

  const formatUsd = (n) =>
    n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

  return (
    <div className="min-h-screen w-full bg-zinc-950 text-zinc-100 flex items-center justify-center p-6">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');
        .font-display { font-family: 'Space Grotesk', sans-serif; }
        .font-body { font-family: 'Inter', sans-serif; }
        .font-mono-data { font-family: 'JetBrains Mono', monospace; }
        .pulse-slider { -webkit-appearance: none; appearance: none; height: 4px; border-radius: 9999px;
          background: linear-gradient(to right, #fbbf24 0%, #fbbf24 var(--fill), #27272a var(--fill), #27272a 100%); }
        .pulse-slider::-webkit-slider-thumb { -webkit-appearance: none; appearance: none; width: 18px; height: 18px;
          border-radius: 9999px; background: #fbbf24; border: 3px solid #09090b; box-shadow: 0 0 0 1px #fbbf24; cursor: pointer; margin-top: -7px; }
        .pulse-slider::-moz-range-thumb { width: 18px; height: 18px; border-radius: 9999px; background: #fbbf24;
          border: 3px solid #09090b; box-shadow: 0 0 0 1px #fbbf24; cursor: pointer; }
        .pulse-slider::-moz-range-track { height: 4px; background: #27272a; border-radius: 9999px; }
      `}</style>

      <div className="font-body w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-xl p-6 sm:p-8">
        <div className="flex items-center gap-2 mb-1">
          <DollarSign className="w-4 h-4 text-amber-400" />
          <span className="font-mono-data text-xs uppercase tracking-[0.15em] text-zinc-500">
            Calculadora de ingresos
          </span>
        </div>
        <h2 className="font-display text-2xl font-semibold tracking-tight mb-6">
          ¿Cuánto podés ganar en YouTube?
        </h2>

        <label className="block text-xs text-zinc-500 mb-1.5" htmlFor="niche-select">Nicho</label>
        <select
          id="niche-select"
          value={selectedNiche ?? ""}
          onChange={(e) => setSelectedNiche(e.target.value)}
          disabled={loading || niches.length === 0}
          className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm mb-6 outline-none focus:border-amber-400/60 transition-colors disabled:opacity-50"
        >
          {niches.map((n) => (
            <option key={n.name} value={n.name}>{n.name}</option>
          ))}
        </select>

        <div className="flex items-center justify-between mb-2">
          <label className="text-xs text-zinc-500 flex items-center gap-1.5" htmlFor="views-slider">
            <Eye className="w-3.5 h-3.5" /> Vistas mensuales
          </label>
          <span className="font-mono-data text-sm text-zinc-100">{monthlyViews.toLocaleString("es-AR")}</span>
        </div>
        <input
          id="views-slider"
          type="range"
          min={0}
          max={100}
          step={1}
          value={sliderPos}
          onChange={(e) => setSliderPos(Number(e.target.value))}
          className="pulse-slider w-full mb-1"
          style={{ "--fill": `${sliderPos}%` }}
        />
        <div className="flex justify-between text-[11px] text-zinc-600 font-mono-data mb-8">
          <span>10K</span><span>1M</span>
        </div>

        <div className="flex items-center justify-between py-3 border-t border-zinc-800 text-sm">
          <span className="text-zinc-500">CPM real ({selectedNiche ?? "—"})</span>
          {loading ? (
            <Loader2 className="w-4 h-4 text-zinc-600 animate-spin" />
          ) : (
            <span className="font-mono-data text-zinc-100">${cpm.toFixed(2)}</span>
          )}
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4">
            <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-1">Por mes</div>
            <div className="font-mono-data text-xl font-semibold text-amber-400 tabular-nums">
              {loading ? "—" : formatUsd(monthlyEarnings)}
            </div>
          </div>
          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4">
            <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-1">Por año</div>
            <div className="font-mono-data text-xl font-semibold text-teal-400 tabular-nums">
              {loading ? "—" : formatUsd(yearlyEarnings)}
            </div>
          </div>
        </div>

        <p className="mt-5 text-[11px] text-zinc-600 leading-relaxed">
          CPM promedio real del nicho, calculado a partir de tus datos en Supabase.
          El ingreso real varía según audiencia, estacionalidad y tipo de contenido.
        </p>
      </div>
    </div>
  );
}

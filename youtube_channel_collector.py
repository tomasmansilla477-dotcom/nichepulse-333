"""
youtube_channel_collector.py

Recolecta estadísticas de canales de YouTube (suscriptores, vistas totales,
promedio de vistas por video, cantidad de videos) usando la YouTube Data API v3,
las guarda en un JSON local y opcionalmente las sube a una tabla de Supabase.

Por qué la API oficial y no scraping:
- Scrapear youtube.com viola los Términos de Servicio de Google/YouTube.
- El HTML de YouTube cambia constantemente y rompe cualquier scraper en semanas.
- La API oficial es gratis hasta 10,000 unidades/día (de sobra para este uso)
  y devuelve datos estructurados y confiables.

Requisitos:
    pip install requests supabase python-dotenv

Variables de entorno esperadas (podés ponerlas en un archivo .env):
    YOUTUBE_API_KEY=tu_api_key_de_google_cloud
    SUPABASE_URL=https://tu-proyecto.supabase.co
    SUPABASE_SERVICE_KEY=tu_service_role_key
"""

import os
import json
import time
from datetime import datetime, timezone

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv es opcional, podés setear las env vars a mano

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

# Cantidad de videos recientes a promediar para "vistas promedio".
VIDEOS_TO_SAMPLE = 10


def get_channel_stats(channel_id: str) -> dict:
    """Trae estadísticas base del canal: suscriptores, vistas totales, cantidad de videos."""
    url = f"{YOUTUBE_API_BASE}/channels"
    params = {
        "part": "snippet,statistics,contentDetails",
        "id": channel_id,
        "key": YOUTUBE_API_KEY,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if not data.get("items"):
        raise ValueError(f"No se encontró el canal con id {channel_id}")

    item = data["items"][0]
    stats = item["statistics"]
    snippet = item["snippet"]
    uploads_playlist_id = item["contentDetails"]["relatedPlaylists"]["uploads"]

    return {
        "channel_id": channel_id,
        "name": snippet.get("title"),
        "subscribers": int(stats.get("subscriberCount", 0)),
        "total_views": int(stats.get("viewCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
        "uploads_playlist_id": uploads_playlist_id,
    }


def get_recent_video_ids(uploads_playlist_id: str, max_results: int = VIDEOS_TO_SAMPLE) -> list:
    """Trae los IDs de los últimos N videos subidos, a partir de la playlist de uploads."""
    url = f"{YOUTUBE_API_BASE}/playlistItems"
    params = {
        "part": "contentDetails",
        "playlistId": uploads_playlist_id,
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return [item["contentDetails"]["videoId"] for item in data.get("items", [])]


def get_average_views(video_ids: list) -> float:
    """Calcula el promedio de vistas de una lista de video IDs."""
    if not video_ids:
        return 0.0

    url = f"{YOUTUBE_API_BASE}/videos"
    params = {
        "part": "statistics",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    view_counts = [int(item["statistics"].get("viewCount", 0)) for item in data.get("items", [])]
    if not view_counts:
        return 0.0
    return round(sum(view_counts) / len(view_counts), 2)


def collect_channel_data(channel_id: str) -> dict:
    """Junta todo: stats del canal + promedio de vistas de los últimos videos."""
    stats = get_channel_stats(channel_id)
    video_ids = get_recent_video_ids(stats["uploads_playlist_id"])
    avg_views = get_average_views(video_ids)

    stats.pop("uploads_playlist_id")  # dato interno, no lo persistimos
    stats["avg_views_last_videos"] = avg_views
    stats["sampled_videos"] = len(video_ids)
    stats["fetched_at"] = datetime.now(timezone.utc).isoformat()
    return stats


def save_to_json(records: list, filepath: str = "channels_data.json") -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"Guardado: {filepath} ({len(records)} canales)")


def upload_to_supabase(records: list, table: str = "youtube_channels") -> None:
    """
    Sube (upsert) los registros a una tabla de Supabase vía REST API.
    La tabla debe tener una columna única (ej. channel_id) para que el upsert
    actualice en vez de duplicar filas en cada corrida.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("Faltan SUPABASE_URL o SUPABASE_SERVICE_KEY: se omite la subida.")
        return

    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",  # upsert por conflicto de PK/unique
    }
    resp = requests.post(url, headers=headers, json=records, timeout=20)

    if resp.status_code in (200, 201):
        print(f"Subido a Supabase: {len(records)} registros en '{table}'")
    else:
        print(f"Error subiendo a Supabase ({resp.status_code}): {resp.text}")


def main():
    if not YOUTUBE_API_KEY:
        raise EnvironmentError("Falta la variable de entorno YOUTUBE_API_KEY")

    # Reemplazá esto por los channel_id reales que quieras trackear.
    # El channel_id NO es el @handle, es el ID que empieza con "UC..."
    # (se obtiene fácilmente buscando "channel id" + el nombre del canal,
    # o vía la propia API con channels.list?forHandle=).
    channel_ids = [
        "UC_x5XG1OV2P6uZZ5FSM9Ttw",  # ejemplo: Google Developers
        "UCsBjURrPoezykLs9EqgamOA",  # ejemplo: Fireship
    ]

    results = []
    for cid in channel_ids:
        try:
            print(f"Procesando canal {cid}...")
            data = collect_channel_data(cid)
            results.append(data)
        except Exception as e:
            print(f"Error con el canal {cid}: {e}")
        time.sleep(0.5)  # margen prudente entre llamadas

    save_to_json(results)
    upload_to_supabase(results)


if __name__ == "__main__":
    main()

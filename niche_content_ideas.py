"""
niche_content_ideas.py

Le manda a Google Gemini las estadísticas de un nicho (volumen de búsqueda,
competencia, etc.) y le pide exactamente 5 ideas de videos virales + 3
preguntas frecuentes, en JSON.

Por qué Gemini y no OpenAI: OpenAI ya no da créditos gratis a cuentas nuevas
(piden mínimo 5 USD prepagos). Gemini sí tiene una capa gratuita real y
generosa (miles de pedidos por día, sin tarjeta de crédito), suficiente para
esta tarea. El código usa "structured output" (responseSchema) para
garantizar que la respuesta sea JSON válido con la forma exacta que
necesitamos, igual que hacíamos con OpenAI.

Requisitos:
    pip install requests python-dotenv

Variables de entorno:
    GEMINI_API_KEY=tu_api_key   (se consigue gratis en aistudio.google.com/apikey)
"""

import os
import json

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

MODEL = "gemini-2.0-flash"  # rápido, gratuito, de sobra para esta tarea
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "video_ideas": {
            "type": "ARRAY",
            "minItems": 5,
            "maxItems": 5,
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "angle": {"type": "STRING"},
                },
                "required": ["title", "angle"],
            },
        },
        "faqs": {
            "type": "ARRAY",
            "minItems": 3,
            "maxItems": 3,
            "items": {
                "type": "OBJECT",
                "properties": {
                    "question": {"type": "STRING"},
                    "answer": {"type": "STRING"},
                },
                "required": ["question", "answer"],
            },
        },
    },
    "required": ["video_ideas", "faqs"],
}


def generate_content_ideas(niche_stats: dict) -> dict:
    prompt = (
        "Sos un estratega de contenido de YouTube especializado en encontrar "
        "ángulos virales dentro de nichos específicos. Basate únicamente en los "
        "datos que te paso, no inventes estadísticas nuevas.\n\n"
        f"Datos del nicho:\n{json.dumps(niche_stats, ensure_ascii=False, indent=2)}\n\n"
        "Generá exactamente 5 ideas de videos con alto potencial viral para este nicho, "
        "y exactamente 3 preguntas frecuentes que la audiencia de este nicho suele buscar, "
        "con su respuesta breve (1-2 oraciones). Respondé en español."
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
        },
    }

    response = requests.post(
        GEMINI_URL,
        params={"key": GEMINI_API_KEY},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(raw_text)


def upload_to_supabase(niche_name: str, result: dict) -> None:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("Faltan SUPABASE_URL o SUPABASE_SERVICE_KEY: se omite la subida.")
        return

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }

    lookup_url = f"{SUPABASE_URL}/rest/v1/niches"
    lookup_resp = requests.get(
        lookup_url,
        headers=headers,
        params={"name": f"eq.{niche_name}", "select": "id"},
        timeout=15,
    )
    lookup_resp.raise_for_status()
    matches = lookup_resp.json()

    if not matches:
        print(f"No existe el nicho '{niche_name}' en la tabla niches. Se omite la subida.")
        return

    niche_id = matches[0]["id"]

    insert_url = f"{SUPABASE_URL}/rest/v1/niche_content_suggestions"
    payload = {
        "niche_id": niche_id,
        "video_ideas": result["video_ideas"],
        "faqs": result["faqs"],
    }
    insert_resp = requests.post(insert_url, headers=headers, json=payload, timeout=15)

    if insert_resp.status_code in (200, 201):
        print(f"Subido a Supabase: ideas de contenido para '{niche_name}'")
    else:
        print(f"Error subiendo a Supabase ({insert_resp.status_code}): {insert_resp.text}")


def save_to_json(niche_name: str, data: dict, filepath: str = None) -> str:
    filepath = filepath or f"{niche_name.lower().replace(' ', '_')}_ideas.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Guardado: {filepath}")
    return filepath


def main():
    if not GEMINI_API_KEY:
        raise EnvironmentError("Falta la variable de entorno GEMINI_API_KEY")

    niche_stats = {
        "niche": "Finanzas Personales",
        "search_volume": 74000,
        "competition": "media",
        "avg_cpm": 12.4,
    }

    print(f"Generando ideas para: {niche_stats['niche']}...")
    result = generate_content_ideas(niche_stats)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    save_to_json(niche_stats["niche"], result)
    upload_to_supabase(niche_stats["niche"], result)


if __name__ == "__main__":
    main()

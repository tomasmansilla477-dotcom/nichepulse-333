"""
niche_content_ideas.py

Le manda a OpenAI las estadísticas de un nicho (volumen de búsqueda, competencia, etc.)
y le pide exactamente 5 ideas de videos virales + 3 preguntas frecuentes, en JSON.

Usa "Structured Outputs" (response_format con json_schema) en vez de solo pedir
JSON por prompt. Esto es importante: con un prompt suelto ("devolveme JSON"),
el modelo puede agregar texto antes/después, olvidar una clave, o romper el
formato — y te explota el json.loads() en producción. Con json_schema, la API
garantiza que la respuesta cumple exactamente esa estructura.

Requisitos:
    pip install openai python-dotenv

Variables de entorno:
    OPENAI_API_KEY=tu_api_key
"""

import os
import json

import requests
from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

MODEL = "gpt-4o-mini"  # buena relación costo/calidad para esta tarea

# Schema que la respuesta del modelo debe cumplir SÍ o SÍ.
RESPONSE_SCHEMA = {
    "name": "niche_content_ideas",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "video_ideas": {
                "type": "array",
                "minItems": 5,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Título del video, estilo clickbait honesto"},
                        "angle": {"type": "string", "description": "Por qué este ángulo puede volverse viral"},
                    },
                    "required": ["title", "angle"],
                    "additionalProperties": False,
                },
            },
            "faqs": {
                "type": "array",
                "minItems": 3,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "answer": {"type": "string", "description": "Respuesta breve, 1-2 oraciones"},
                    },
                    "required": ["question", "answer"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["video_ideas", "faqs"],
        "additionalProperties": False,
    },
}


def generate_content_ideas(niche_stats: dict) -> dict:
    """
    niche_stats esperado, por ejemplo:
    {
        "niche": "Finanzas Personales",
        "search_volume": 74000,
        "competition": "media",
        "avg_cpm": 12.4
    }
    """
    system_prompt = (
        "Sos un estratega de contenido de YouTube especializado en encontrar "
        "ángulos virales dentro de nichos específicos. Basate únicamente en los "
        "datos que te pasan, no inventes estadísticas nuevas."
    )

    user_prompt = (
        f"Datos del nicho:\n{json.dumps(niche_stats, ensure_ascii=False, indent=2)}\n\n"
        "Generá exactamente 5 ideas de videos con alto potencial viral para este nicho, "
        "y exactamente 3 preguntas frecuentes que la audiencia de este nicho suele buscar, "
        "con su respuesta breve. Respondé en español."
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": RESPONSE_SCHEMA,
        },
        temperature=0.8,  # un poco de creatividad para los títulos, sin perder foco
    )

    # Con Structured Outputs esto SIEMPRE es JSON válido con esta forma exacta,
    # así que el parseo nunca debería fallar por formato.
    return json.loads(response.choices[0].message.content)


def upload_to_supabase(niche_name: str, result: dict) -> None:
    """Busca el id del nicho por nombre y guarda las ideas/FAQs en niche_content_suggestions."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("Faltan SUPABASE_URL o SUPABASE_SERVICE_KEY: se omite la subida.")
        return

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }

    # 1) Buscar el id del nicho por nombre.
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

    # 2) Insertar las ideas + FAQs asociadas a ese nicho.
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
    # Ejemplo: esto normalmente vendría de tu base de Supabase (la tabla que
    # armamos en el script anterior), no hardcodeado.
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

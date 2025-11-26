import os
import json
import threading
import time
from urllib.parse import quote
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

from src.constants import SAUDACOES_WORDS, SAUDACOES_PHRASES, IDENTITY_KEYWORDS
from src.utils import load_prompt_data, normalize_text
from src.search import build_search_index, find_item_smart
from src.llm import conversar_com_chat
from src.logger import log_interaction

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
PROMPT_FILE = os.path.join(APP_ROOT, "data", "prompt.json")

app = Flask(__name__)

redis_url = os.getenv("REDIS_URL")
storage_uri = redis_url if redis_url else "memory://"
cache_config = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_REDIS_URL': redis_url
} if redis_url else {'CACHE_TYPE': 'SimpleCache'}

limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"], storage_uri=storage_uri)
cache = Cache(app, config=cache_config)

prompt_data = load_prompt_data(PROMPT_FILE)
system_prompt = "\n".join(prompt_data.get("system_prompt", [])) if prompt_data else None
if prompt_data:
    build_search_index(prompt_data)

def create_search_map_link(query: str) -> str:
    full_query = quote(f"{query}, Axixá, Maranhão")
    return f"https://www.google.com/maps/search/?api=1&query={full_query}"

def responder_rapido(pergunta, resposta, tipo_log):
    threading.Thread(target=log_interaction, args=(pergunta, resposta, tipo_log)).start()
    return jsonify({"resposta": resposta, "mapa_link": None, "local_nome": tipo_log})

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
@limiter.limit("10 per minute")
def chat():
    start_time = time.time()
    data = request.json
    pergunta = data.get("pergunta", "")
    historico = data.get("historico", [])
    
    if not pergunta:
        return jsonify({"erro": "Pergunta vazia"}), 400
    if len(pergunta) > 500:
        return jsonify({"erro": "Sua pergunta é muito longa (max 500 caracteres)."}), 400

    texto_input = normalize_text(pergunta)
    
    palavras_input = set(texto_input.split())
    if (palavras_input & SAUDACOES_WORDS) or any(p in texto_input for p in SAUDACOES_PHRASES):
        return responder_rapido(pergunta, "Olá! Sou o Guia Digital de Axixá. Posso ajudar com escolas, lojas, turismo e história da cidade.", "Saudação")
    
    if any(k in texto_input for k in IDENTITY_KEYWORDS):
        return responder_rapido(pergunta, "Desenvolvido por: Guilherme Moreira, José Ribamar, Marina de Jesus e Rikelmy Rabelo.", "Créditos")

    item_data_json = None
    local_nome = None
    mapa_link = None
    item_encontrado = None

    if "historia" in texto_input:
        item_data_json = json.dumps(prompt_data.get("historia_axixa"), ensure_ascii=False)
        local_nome = "História"
    elif "comida" in texto_input and "quais" in texto_input:
        item_data_json = json.dumps(prompt_data.get("comidas_tipicas"), ensure_ascii=False)
        local_nome = "Comidas Típicas"
    else:
        item_encontrado = find_item_smart(pergunta)

    if item_encontrado and not item_data_json:
        item_encontrado_copy = dict(item_encontrado)
        if item_encontrado_copy.get("is_general"):
            cat = item_encontrado_copy.get("category", "").lower()
            if cat in ("escolas", "lojas", "igrejas"):
                item_encontrado_copy["description"] = (
                    str(item_encontrado_copy.get("description", "")) + " povoados"
                )
        item_data_json = json.dumps(item_encontrado_copy, ensure_ascii=False)
        
        if item_encontrado.get("is_general"):
            local_nome = f"Geral: {item_encontrado.get('category')}"
        else:
            local_nome = item_encontrado.get("nome") or item_encontrado.get("orgao")
            endereco = item_encontrado.get("localizacao") or item_encontrado.get("endereco") or ""
            if len(endereco) > 5 and "rural" not in endereco.lower():
                mapa_link = create_search_map_link(f"{local_nome}, {endereco}")
            else:
                mapa_link = create_search_map_link(local_nome)

    def generate():
        yield json.dumps({"mapa_link": mapa_link, "local_nome": local_nome}) + "\n"
        
        full_response = ""
        for chunk in conversar_com_chat(pergunta, system_prompt, item_data_json, historico):
            full_response += chunk
            yield chunk
        
        threading.Thread(target=log_interaction, args=(pergunta, full_response, local_nome)).start()
        print(f"\033[92m[Latência] Total: {time.time() - start_time:.2f}s\033[0m")

    return Response(stream_with_context(generate()), mimetype='text/plain')

if __name__ == "__main__":
    app.run(debug=True)
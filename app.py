import os
import json
import threading
import urllib.parse
from flask import Flask, request, jsonify, render_template
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

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

prompt_data = load_prompt_data(PROMPT_FILE)
if prompt_data:
    system_prompt = "\n".join(prompt_data.get("system_prompt", []))
    build_search_index(prompt_data) 
else:
    system_prompt = None

def create_search_map_link(query: str) -> str:
    full_query = f"{query}, Axixá, Maranhão"
    encoded = urllib.parse.quote(full_query)
    return f"https://www.google.com/maps/search/?api=1&query={encoded}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
@limiter.limit("10 per minute")
def chat():
    data = request.json
    pergunta = data.get("pergunta", "")
    historico = data.get("historico", [])
    
    if not pergunta:
        return jsonify({"erro": "Pergunta vazia"}), 400

    if len(pergunta) > 500:
        return jsonify({
            "erro": "Sua pergunta é muito longa. Por favor, limite-se a 500 caracteres."
        }), 400

    texto_input = normalize_text(pergunta)
    palavras_input = set(texto_input.split())
    is_saudacao_word = bool(palavras_input & SAUDACOES_WORDS)
    is_saudacao_phrase = any(p in texto_input for p in SAUDACOES_PHRASES)

    if is_saudacao_word or is_saudacao_phrase:
        resp = "Olá! Sou o Guia Digital de Axixá. Posso ajudar com escolas, lojas, turismo e história da cidade."
        threading.Thread(target=log_interaction, args=(pergunta, resp, "Saudação")).start()
        return jsonify({"resposta": resp, "mapa_link": None, "local_nome": "Saudação"})
    
    if any(k in texto_input for k in IDENTITY_KEYWORDS):
        resp = "Desenvolvido por: Guilherme Moreira, José Ribamar, Marina de Jesus e Rikelmy Rabelo."
        threading.Thread(target=log_interaction, args=(pergunta, resp, "Créditos")).start()
        return jsonify({"resposta": resp, "mapa_link": None, "local_nome": "Créditos"})

    cache_key = normalize_text(pergunta)
    
    if not data.get("historico") and cache.get(cache_key):
        return jsonify(cache.get(cache_key))

    item_encontrado = None
    item_data_json = None
    local_nome = None
    mapa_link = None

    if "historia" in texto_input:
        item_data_json = json.dumps(prompt_data.get("historia_axixa"), ensure_ascii=False)
        local_nome = "História"
    elif "comida" in texto_input and "quais" in texto_input:
        item_data_json = json.dumps(prompt_data.get("comidas_tipicas"), ensure_ascii=False)
        local_nome = "Comidas Típicas"
    else:
        item_encontrado = find_item_smart(pergunta)

    if item_encontrado and not item_data_json:
        item_data_json = json.dumps(item_encontrado, ensure_ascii=False)
        
        if item_encontrado.get("is_general"):
            local_nome = f"Geral: {item_encontrado.get('category')}"
            mapa_link = None
        else:
            local_nome = item_encontrado.get("nome") or item_encontrado.get("orgao")
            endereco = item_encontrado.get("localizacao") or item_encontrado.get("endereco")
            
            if endereco and len(endereco) > 5 and "rural" not in endereco.lower():
                mapa_link = create_search_map_link(f"{local_nome}, {endereco}")
            else:
                mapa_link = create_search_map_link(local_nome)

    try:
        resposta_ia = conversar_com_chat(pergunta, system_prompt, item_data_json, historico)

        if isinstance(resposta_ia, str) and "[Erro" in resposta_ia:
            return jsonify({"erro": "Erro no processamento da IA"}), 500

        threading.Thread(target=log_interaction, args=(pergunta, resposta_ia, local_nome)).start()

        response_data = {
            "resposta": resposta_ia,
            "mapa_link": mapa_link,
            "local_nome": local_nome
        }

        if not data.get("historico"):
            cache.set(cache_key, response_data, timeout=300)

        return jsonify(response_data)
    except Exception as e:
        print(f"Erro interno: {e}")
        return jsonify({"erro": "Ocorreu um erro interno no servidor."}), 500

if __name__ == "__main__":
    app.run(debug=True)
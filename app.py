import requests
import os
import json
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
import urllib.parse
import re
import unicodedata

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-chat"

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
PROMPT_FILE = os.path.join(APP_ROOT, "prompt.json")

app = Flask(__name__)

STOP_WORDS = {
    'a', 'o', 'e', 'ou', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 
    'nos', 'nas', 'por', 'para', 'com', 'sem', 'sob', 'sobre', 
    'me', 'fale', 'diga', 'onde', 'fica', 'localiza', 'localizacao', 'qual', 'e',
    'gostaria', 'queria', 'quero', 'saber', 'informacoes', 'info', 'axixa',
    'tem', 'tinha', 'existe', 'ha', 'algum', 'alguma', 'uns', 'umas', 'um', 'uma',
    'banho', 'tomar', 'ir', 'chegar', 'encontrar',
    'loja', 'lojas', 'comprar',
    'escola', 'escolas', 'colegio',
    'secretaria', 'municipal',
    'igreja', 'paroquia',
    'cemiterio',
    'praca',
    'ginasio', 'campo',
    'pousada', 'hotel'
}


def sanitize_data(data):
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            clean_key = k.strip().lower()
            clean_key = unicodedata.normalize('NFKD', clean_key).encode('ASCII', 'ignore').decode('utf-8')
            new_dict[clean_key] = sanitize_data(v)
        return new_dict
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    else:
        return data

def load_prompt_data(file_path: str) -> dict:
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        return sanitize_data(data)
    except Exception as e:
        print(f"[Erro] {e}")
        return None

prompt_data = load_prompt_data(PROMPT_FILE)
 
if prompt_data:
    system_prompt = "\n".join(prompt_data.get("system_prompt", []))
else:
    system_prompt = None

def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s]', '', text)
    return text

def get_all_text_content(item):
    content = ""
    for value in item.values():
        if isinstance(value, str):
            content += " " + value
    return normalize_text(content)

def get_fuzzy_value(item, candidates):
    for key, value in item.items():
        if any(c in key for c in candidates):
            return value
    return ""

def find_item_by_name(pergunta_lower: str, data: dict):
    if not data:
        return None, None

    pergunta_limpa = normalize_text(pergunta_lower)
    keywords = {w for w in pergunta_limpa.split() if w not in STOP_WORDS and len(w) > 2}

    if not keywords:
        return None, None

    best_item = None
    best_score = 0

    lists = ["pontos_turisticos", "igrejas", "lojas", "escolas", "predios_municipais", "campos_esportivos", "cemiterios", "pousadas_dormitorios"]

    for key in lists:
        for item in data.get(key, []):
            text = get_all_text_content(item)
            score = sum(1 for k in keywords if k in text)
            if score > best_score:
                best_score = score
                best_item = item

    return best_item, None

def conversar_com_guia(pergunta: str, system_prompt: str, item_data_json: str = None):
    if os.getenv("MODO_TESTE") == "True":
        return "Resposta simulada (Modo Teste)"

    if not system_prompt:
        return "[Erro crítico]"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://seusite.com",
        "X-Title": "Guia Digital - LocalizAxixá",
    }

    messages = [{"role": "system", "content": system_prompt}]

    if item_data_json:
        messages.append({
            "role": "system",
            "content": f"INSTRUÇÃO IMPORTANTE: Você encontrou dados locais para a pergunta. Responda usando APENAS estes dados: {item_data_json}"
        })

    messages.append({"role": "user", "content": pergunta})

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 1024
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Erro na IA: {e}]"

def create_search_map_link(query: str) -> str:
    full_query = f"{query}, Axixá, Maranhão"
    encoded_query = urllib.parse.quote(full_query)
    return f"https://www.google.com/maps/search/{encoded_query}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    pergunta = data.get("pergunta")
    pergunta_lower = pergunta.lower() if pergunta else ""

    if not pergunta:
        return jsonify({"erro": "Nenhuma pergunta fornecida."}), 400

    item_encontrado = None
    mapa_link = None
    local_nome = None
    item_data_json = None
    
    if prompt_data:
        termos_historia = [
            "história", "historia", "fundação", "fundacao", "origem", 
            "fundou", "criou", "surgiu", "começou", 
            "cultura", "folclore", "bumba", "boi", "festa",
            "prato", "comida", "tipico", "típico", "economia", "produz",
            "arroz", "cuxa", "cuxá"
        ]
        is_historia = any(word in pergunta_lower for word in termos_historia)

        if is_historia:
            historia_data = prompt_data.get("historia_axixa")
            if historia_data:
                item_data_json = json.dumps(historia_data, ensure_ascii=False)
        else:
            pergunta_normalizada = normalize_text(pergunta_lower)
            
            regras_categoria = {
                "campos_esportivos": ["quadra", "campo", "ginasio", "estadio"],
                "igrejas": ["igreja", "paroquia", "religiao", "matriz"],
                "lojas": ["loja", "comprar", "mercado", "farmacia", "vende", "material", "materiais", "construcao", "moda", "calcados"],
                "escolas": ["escola", "colegio", "estudar", "iema", "creche", "infancia"],
                "predios_municipais": ["prefeitura", "secretaria", "cras", "camara", "vereador", "vereadores", "semed", "semus", "semaf"],
                "pontos_turisticos": ["turismo", "passear", "banho", "rio", "balneario", "praca"],
                "cemiterios": ["cemiterio"],
                "pousadas_dormitorios": ["pousada", "hotel", "dormir"]
            }

            categoria_selecionada = None
            for chave_json, gatilhos in regras_categoria.items():
                if any(g in pergunta_normalizada for g in gatilhos):
                    categoria_selecionada = chave_json
                    break
            termos_busca = set(pergunta_normalizada.split()) - STOP_WORDS

            if not termos_busca:
                basic_stops = {'a', 'o', 'de', 'em', 'para', 'com', 'onde', 'fica'}
                termos_busca = set(pergunta_normalizada.split()) - basic_stops

            if categoria_selecionada:
                dados_raw = prompt_data.get(categoria_selecionada, [])
                melhor_item = None
                maior_score = 0

                for item in dados_raw:
                    texto = get_all_text_content(item)
                    score = sum(1 for t in termos_busca if t in texto)
                    if score > maior_score:
                        maior_score = score
                        melhor_item = item
                
                if melhor_item and maior_score > 0:
                    item_encontrado = melhor_item
                    item_data_json = json.dumps(item_encontrado, ensure_ascii=False)

            if not item_data_json:
                item_global, _ = find_item_by_name(pergunta_lower, prompt_data)
                if item_global:
                    item_encontrado = item_global
                    item_data_json = json.dumps(item_encontrado, ensure_ascii=False)

    if item_encontrado: 
        local_nome = get_fuzzy_value(item_encontrado, ["nome", "orgao", "titulo"])
        if not local_nome: local_nome = list(item_encontrado.values())[0]
        
        endereco = get_fuzzy_value(item_encontrado, ["localizacao", "endereco"])
        
        query_mapa = local_nome
        if endereco and isinstance(endereco, str) and endereco.lower() not in ["centro", "zona rural"]:
            query_mapa = f"{local_nome}, {endereco}"
        mapa_link = create_search_map_link(query_mapa)
    
    resposta_ia = conversar_com_guia(pergunta, system_prompt, item_data_json)

    return jsonify({"resposta": resposta_ia, "mapa_link": mapa_link, "local_nome": local_nome})

if __name__ == "__main__":
    app.run(debug=True)
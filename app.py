import requests
import os
import json
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
import urllib.parse
import re

app = Flask(__name__)

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-chat"
PROMPT_FILE = "prompt.json"

def load_prompt_data(file_path: str) -> dict:
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"[Erro] Ocorreu um erro ao ler o {file_path}: {e}")
        return None

prompt_data = load_prompt_data(PROMPT_FILE)
system_prompt = "\n".join(prompt_data.get("system_prompt", [])) if prompt_data else None

def conversar_com_valdir(pergunta: str, system_prompt: str, item_data_json: str = None):
    
    if not system_prompt:
        return "[Erro crítico: O prompt do sistema não foi carregado.]"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https.seu-site-ou-projeto.com",
        "X-Title": "Guia Digital Valdir Moraes",
    }
    
    messages = [{"role": "system", "content": system_prompt}]
    
    if item_data_json:
        messages.append({
            "role": "system", 
            "content": f"INSTRUÇÃO IMPORTANTE: Você encontrou dados locais para a pergunta do usuário. Responda à pergunta do usuário de forma natural e apresente *apenas* os dados factuais fornecidos abaixo. Siga as regras de formatação do seu prompt principal. DADOS FACTUAIS: {item_data_json}"
        })
    
    messages.append({"role": "user", "content": pergunta})

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 300
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status() 
        data = response.json()

        content = data["choices"][0]["message"]["content"]
        return content.strip()

    except requests.exceptions.RequestException as e:
        return f"[Erro de conexão com a API: {e}]"
    except KeyError:
        return f"[Erro: resposta inesperada da API: {data}]"
    except Exception as e:
        return f"[Erro inesperado: {e}]"

def find_item_by_name(pergunta_lower: str, data: dict):
    if not data or not pergunta_lower:
        return None, None

    pergunta_limpa = re.sub(r'[^\w\s]', '', pergunta_lower)
    
    stop_words = {
        'a', 'o', 'e', 'ou', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 
        'nos', 'nas', 'por', 'para', 'com', 'sem', 'sob', 'sobre', 
        'me', 'fale', 'diga', 'onde', 'fica', 'localiza', 'qual', 'é',
        'escola', 'igreja', 'loja', 'campo', 'ginásio', 'prefeitura',
        'secretaria', 'prédio', 'tem'
    }
    
    pergunta_keywords = {
        word for word in pergunta_limpa.split() if word not in stop_words and len(word) > 2
    }
    
    if not pergunta_keywords:
        return None, None

    lists_to_search = ["pontos_turisticos", "igrejas", "lojas", "escolas", "predios_municipais", "campos_esportivos"]
    
    found_item = None
    found_key = None
    best_match_score = 0

    for key in lists_to_search:
        for item in data.get(key, []):
            nome_completo = (item.get("nome", "") or item.get("orgao", "")).lower()
            if not nome_completo:
                continue

            nome_limpo = re.sub(r'[^\w\s]', '', nome_completo)
            
            current_match_score = 0
            for keyword in pergunta_keywords:
                if keyword in nome_limpo:
                    current_match_score += len(keyword)
            
            if current_match_score > best_match_score:
                best_match_score = current_match_score
                found_item = item
                found_key = key
                        
    return found_item, found_key

def create_search_map_link(query: str) -> str:
    full_query = f"{query}, Axixá, Maranhão"
    encoded_query = urllib.parse.quote(full_query)
    
    return f"https://www.google.com/maps?q={encoded_query}"

app = Flask(__name__, template_folder='public')

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
    category_key = None
    mapa_link = None
    local_nome = None
    item_data_json = None
    
    is_historia = any(word in pergunta_lower for word in ["história", "historia", "fundação", "fundacao", "origem"])

    if is_historia:
        historia_data = prompt_data.get("historia_axixa")
        if historia_data:
            item_data_json = json.dumps(historia_data, ensure_ascii=False)
    else:
        item_encontrado, category_key = find_item_by_name(pergunta_lower, prompt_data)

    if item_encontrado:
        item_data_json = json.dumps(item_encontrado, ensure_ascii=False)
        
        local_nome = item_encontrado.get("nome") or item_encontrado.get("orgao")
        endereco = item_encontrado.get("localizacao") or item_encontrado.get("endereco")
        
        query_mapa = local_nome
        if endereco:
            query_mapa = f"{local_nome}, {endereco}"
        mapa_link = create_search_map_link(query_mapa)
    
    if not system_prompt:
        return jsonify({"erro": "Prompt do sistema não carregado no servidor."}), 500
    
    resposta_ia = conversar_com_valdir(pergunta, system_prompt, item_data_json)

    return jsonify({"resposta": resposta_ia, "mapa_link": mapa_link, "local_nome": local_nome})

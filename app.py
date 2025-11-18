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

def load_prompt_data(file_path: str) -> dict:
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"[Erro] Ocorreu um erro ao ler o {file_path}: {e}")
        return None

prompt_data = load_prompt_data(PROMPT_FILE)
 
if prompt_data:
    system_prompt = "\n".join(prompt_data.get("system_prompt", []))
else:
    system_prompt = None

def conversar_com_guia(pergunta: str, system_prompt: str, item_data_json: str = None):
    
    if not system_prompt:
        return "[Erro crítico: O prompt do sistema não foi carregado.]"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https.seu-site-ou-projeto.com",
        "X-Title": "Guia Digital - LocalizAxixá",
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
        "max_tokens": 1024
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

def normalize_text(text: str) -> str:
    if not text: return ""
    text = text.lower()
    text = re.sub(r'[áàâãä]', 'a', text)
    text = re.sub(r'[éèêë]', 'e', text)
    text = re.sub(r'[íìîï]', 'i', text)
    text = re.sub(r'[óòôõö]', 'o', text)
    text = re.sub(r'[úùûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text

def find_item_by_name(pergunta_lower: str, data: dict):
    if not data or not pergunta_lower:
        return None, None

    pergunta_limpa = normalize_text(pergunta_lower)
    
    stop_words = {
        'a', 'o', 'e', 'ou', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 
        'nos', 'nas', 'por', 'para', 'com', 'sem', 'sob', 'sobre', 
        'me', 'fale', 'diga', 'onde', 'fica', 'localiza', 'localizacao', 'qual', 'e',
        'gostaria', 'queria', 'saber', 'informacoes', 'info', 'axixa',
        'loja', 'lojas'
    }
    
    pergunta_keywords = {
        word for word in pergunta_limpa.split() if word not in stop_words and len(word) > 2
    }
    
    if not pergunta_keywords:
        return None, None

    lists_to_search = ["pontos_turisticos", "igrejas", "lojas", "escolas", "predios_municipais", "campos_esportivos", "cemiterios", "pousadas_dormitorios"]
    
    found_item = None
    found_key = None
    best_match_score = 0

    for key in lists_to_search:
        for item in data.get(key, []):
            nome = (item.get("nome", "") or item.get("orgao", ""))
            local = (item.get("localizacao", "") or item.get("endereco", ""))
            search_text_limpo = normalize_text(nome + " " + local)
            
            if not search_text_limpo.strip():
                continue
            
            current_match_score = 0
            for keyword in pergunta_keywords:
                if keyword in search_text_limpo:
                    current_match_score += len(keyword)
            
            if current_match_score > best_match_score:
                best_match_score = current_match_score
                found_item = item
                found_key = key
                        
    return found_item, found_key

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
    category_key = None
    mapa_link = None
    local_nome = None
    item_data_json = None
    
    stop_words_list = {
        'a', 'o', 'e', 'ou', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 
        'nos', 'nas', 'por', 'para', 'com', 'sem', 'sob', 'sobre', 
        'me', 'fale', 'diga', 'onde', 'fica', 'localiza', 'localizacao', 'qual', 'e',
        'gostaria', 'queria', 'saber', 'informacoes', 'info', 'axixa'
    }

    if prompt_data:
        is_historia = any(word in pergunta_lower for word in ["história", "historia", "fundação", "fundacao", "origem"])

        if is_historia:
            historia_data = prompt_data.get("historia_axixa")
            if historia_data:
                item_data_json = json.dumps(historia_data, ensure_ascii=False)
        else:
            categoria_encontrada = None
            pergunta_normalizada = normalize_text(pergunta_lower)
            pergunta_normalizada_set = set(pergunta_normalizada.split())
            
            categoria_keywords = {}
            
            if any(word in pergunta_normalizada for word in ["quadra", "quadras", "campo", "campos", "esporte", "esportivos", "ginasio", "ginasios"]):
                categoria_encontrada = "campos_esportivos"
                categoria_keywords = {"quadra", "quadras", "campo", "campos", "esporte", "esportivos", "ginasio", "ginasios"}
            elif any(word in pergunta_normalizada for word in ["igreja", "igrejas", "paroquia", "paroquias", "religiao", "religioso"]):
                categoria_encontrada = "igrejas"
                categoria_keywords = {"igreja", "igrejas", "paroquia", "paroquias", "religiao", "religioso"}
            elif any(word in pergunta_normalizada for word in ["loja", "lojas", "comprar", "comercio", "mercado", "farmacia"]):
                categoria_encontrada = "lojas"
                categoria_keywords = {"loja", "lojas", "comprar", "comercio", "mercado", "farmacia"}
            elif any(word in pergunta_normalizada for word in ["escola", "escolas", "colegio", "colegios", "estudar", "iema"]):
                categoria_encontrada = "escolas"
                categoria_keywords = {"escola", "escolas", "colegio", "colegios", "estudar", "iema"}
            elif any(word in pergunta_normalizada for word in ["prefeitura", "predio municipal", "predios municipais", "secretaria", "secretarias"]):
                categoria_encontrada = "predios_municipais"
                categoria_keywords = {"prefeitura", "predio", "municipal", "predios", "municipais", "secretaria", "secretarias"}
            elif any(word in pergunta_normalizada for word in ["ponto turistico", "pontos turisticos", "turismo", "passear", "visitar", "praca", "pracas", "banho", "rio", "balneario", "balnearios", "historico", "historicos", "ruina", "ruinas"]):
                categoria_encontrada = "pontos_turisticos"
                categoria_keywords = {"ponto", "pontos", "turistico", "turisticos", "turismo", "passear", "visitar", "praca", "pracas", "banho", "rio", "balneario", "balnearios", "historico", "historicos", "ruina", "ruinas"}
            elif any(word in pergunta_normalizada for word in ["cemiterio", "cemiterios"]):
                categoria_encontrada = "cemiterios"
                categoria_keywords = {"cemiterio", "cemiterios"}
            elif any(word in pergunta_normalizada for word in ["pousada", "pousadas", "dormir", "hotel", "hoteis", "hospedagem", "hospedagens", "dormitorio", "dormitorios"]):
                categoria_encontrada = "pousadas_dormitorios"
                categoria_keywords = {"pousada", "pousadas", "dormir", "hotel", "hoteis", "hospedagem", "hospedagens", "dormitorio", "dormitorios"}
            
            if categoria_encontrada:
                dados_categoria = prompt_data.get(categoria_encontrada)
                
                sub_keywords = pergunta_normalizada_set - categoria_keywords - stop_words_list
                
                if sub_keywords and dados_categoria:
                    filtered_data = []
                    for item in dados_categoria:
                        texto_busca = (item.get("descricao", "") + " " + 
                                      (item.get("nome", "") or item.get("orgao", "")) + " " + 
                                      (item.get("localizacao", "") or item.get("endereco", "")))
                        search_text = normalize_text(texto_busca)
                        
                        if all(kw in search_text for kw in sub_keywords):
                            filtered_data.append(item)
                    
                    if filtered_data:
                        dados_categoria = filtered_data
                
                if dados_categoria:
                    if len(dados_categoria) == 1:
                        item_encontrado = dados_categoria[0]
                        item_data_json = json.dumps(item_encontrado, ensure_ascii=False)
                    else:
                        item_data_json = json.dumps(dados_categoria, ensure_ascii=False)

            if not item_data_json:
                item_encontrado, category_key = find_item_by_name(pergunta_lower, prompt_data)
                if item_encontrado:
                    item_data_json = json.dumps(item_encontrado, ensure_ascii=False)

    if item_encontrado: 
        local_nome = item_encontrado.get("nome") or item_encontrado.get("orgao")
        endereco = item_encontrado.get("localizacao") or item_encontrado.get("endereco")
        
        query_mapa = local_nome
        if endereco and endereco.lower() not in ["centro", "zona rural", "belém - zona rural"]:
            query_mapa = f"{local_nome}, {endereco}"
        mapa_link = create_search_map_link(query_mapa)
    
    if not system_prompt:
        return jsonify({"erro": "Prompt do sistema não carregado no servidor."}), 500
    
    resposta_ia = conversar_com_guia(pergunta, system_prompt, item_data_json)

    return jsonify({"resposta": resposta_ia, "mapa_link": mapa_link, "local_nome": local_nome})
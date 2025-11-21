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

def conversar_com_chat(pergunta: str, system_prompt: str, item_data_json: str = None):
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
        'me', 'fale', 'diga', 'onde', 'fica', 'localiza', 'localizacao', 'qual', 'quais', 'sao', 'sou',
        'gostaria', 'queria', 'saber', 'informacoes', 'info', 'axixa', 'cidade', 'municipio',
        'ola', 'oi', 'como', 'faco', 'pra', 'chegar', 'quero',
        'tem', 'tinha', 'existe', 'ha', 'que', 'alguma', 'algum', 'uns', 'umas',
        'loja', 'lojas', 'bairro', 'rua', 'av', 'avenida', 'povoado'
    }
    
    pergunta_keywords = {
        word for word in pergunta_limpa.split() if word not in stop_words and len(word) > 2
    }
    
    if not pergunta_keywords:
        return None, None

    category_keywords_map = {
        "escolas": ["escola", "colegio", "creche", "estudar", "ensino", "infancia", "fundamental", "medio", "educacao", "unidade"],
        "lojas": ["comprar", "mercado", "vende", "roupa", "moda", "moveis", "eletro", "calcados", "flor", "variedade", "material"],
        "pontos_turisticos": ["turismo", "passear", "banho", "rio", "praca", "igreja", "visitar", "ruina", "lazer", "turistico", "historico"],
        "igrejas": ["igreja", "paroquia", "culto", "missa", "evangelica", "catolica", "assembleia", "batista"],
        "predios_municipais": ["prefeitura", "secretaria", "cras", "camara", "orgao", "publico"],
        "campos_esportivos": ["campo", "futebol", "ginasio", "jogo", "esporte", "quadra", "bola"],
        "cemiterios": ["cemiterio", "sepultamento", "enterrar"],
        "pousadas_dormitorios": ["pousada", "dormir", "hotel", "hospedagem", "quarto", "dormitorio"],
        "comidas_tipicas": ["comida", "tipica", "prato", "fome", "comer", "restaurante", "gastronomia", "culinaria", "almoco", "jantar", "peixe", "jucara"]
    }

    lists_to_search = ["pontos_turisticos", "igrejas", "lojas", "escolas", "predios_municipais", "campos_esportivos", "cemiterios", "pousadas_dormitorios", "comidas_tipicas"]
    
    found_item = None
    found_key = None
    best_match_score = 0
    
    MIN_SCORE_THRESHOLD = 15

    for key in lists_to_search:
        category_bonus = 0
        category_terms = category_keywords_map.get(key, [])
        
        if any(kw in pergunta_limpa for kw in category_terms):
            category_bonus = 50

        for item in data.get(key, []):
            nome = item.get("nome", "") or item.get("orgao", "")
            descricao = item.get("descricao", "")
            localizacao = item.get("localizacao", "") or item.get("endereco", "")
            
            nome_limpo = normalize_text(nome)
            full_text_search = normalize_text(f"{nome} {descricao} {localizacao}")
            
            current_match_score = category_bonus
            matched_keywords_count = 0
            
            for keyword in pergunta_keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                
                if re.search(pattern, full_text_search):
                    matched_keywords_count += 1
                    if re.search(pattern, nome_limpo):
                        current_match_score += (len(keyword) * 3)
                    else:
                        current_match_score += len(keyword)
            
            if matched_keywords_count > 0:
                if current_match_score > best_match_score:
                    best_match_score = current_match_score
                    found_item = item
                    found_key = key
                        
    if best_match_score < MIN_SCORE_THRESHOLD:
        return None, None
        
    return found_item, found_key

def create_search_map_link(query: str) -> str:
    full_query = f"{query}, Axixá, Maranhão"
    encoded_query = urllib.parse.quote(full_query)
    return f"http://googleusercontent.com/maps/google.com/0{encoded_query}"

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
        criador_keywords = ["quem fez", "quem criou", "quem desenvolveu", "criador", "desenvolvedor", "quem e voce", "quem é voce", "quem é você"]
        if any(phrase in pergunta_lower for phrase in criador_keywords):
             resposta_criador = (
                 "Sou o Guia Digital - LocalizAxixá, desenvolvido por:\n\n"
                 "**Guilherme Moreira Santos**\n"
                 "**José Ribamar Andrade Santos Júnior**\n"
                 "**Marina de Jesus Lima Muniz**\n"
                 "**Rikelmy Rabelo Freitas**\n\n"
                 "Estou aqui para ajudar com informações sobre a cidade!"
             )
             return jsonify({"resposta": resposta_criador, "mapa_link": None, "local_nome": "Info dos Criadores"})

        historia_keywords = ["história", "historia", "fundação", "fundacao", "origem", "emancipação", "emancipacao", "fundou", "criou", "economia", "cultura", "bumba"]
        is_historia = any(word in pergunta_lower for word in historia_keywords)

        if is_historia:
            historia_data = prompt_data.get("historia_axixa")
            if historia_data:
                item_data_json = json.dumps(historia_data, ensure_ascii=False)
        
        elif "comida" in pergunta_lower or "prato" in pergunta_lower or "comer" in pergunta_lower:
            if any(x in pergunta_lower for x in ["quais", "lista", "todas", "tipos"]):
                 comidas = prompt_data.get("comidas_tipicas", [])
                 if comidas:
                     item_data_json = json.dumps(comidas, ensure_ascii=False)
            else:
                item_encontrado, _ = find_item_by_name(pergunta_lower, prompt_data)
        
        else:
            item_encontrado, _ = find_item_by_name(pergunta_lower, prompt_data)
    
    if item_encontrado and not item_data_json: 
        item_data_json = json.dumps(item_encontrado, ensure_ascii=False)
        local_nome = item_encontrado.get("nome") or item_encontrado.get("orgao")
        endereco = item_encontrado.get("localizacao") or item_encontrado.get("endereco")
        
        query_mapa = local_nome
        if endereco and normalize_text(endereco) not in ["centro", "zona rural", "belem zona rural"]:
            query_mapa = f"{local_nome}, {endereco}"
        mapa_link = create_search_map_link(query_mapa)
    
    if not system_prompt:
        return jsonify({"erro": "Prompt do sistema não carregado no servidor."}), 500
    
    resposta_ia = conversar_com_chat(pergunta, system_prompt, item_data_json)

    return jsonify({"resposta": resposta_ia, "mapa_link": mapa_link, "local_nome": local_nome})

if __name__ == "__main__":
    app.run(debug=True)
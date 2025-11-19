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
        print(f"[Erro] {e}")
        return None

prompt_data = load_prompt_data(PROMPT_FILE)
 
if prompt_data:
    system_prompt = "\n".join(prompt_data.get("system_prompt", []))
else:
    system_prompt = None

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

def normalize_text(text: str) -> str:
    if not text: return ""
    text = text.lower()
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s]', '', text)
    return text

STOP_WORDS = {
    'a', 'o', 'e', 'ou', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 
    'nos', 'nas', 'por', 'para', 'com', 'sem', 'sob', 'sobre', 
    'me', 'fale', 'diga', 'onde', 'fica', 'localiza', 'localizacao', 'qual', 'e',
    'gostaria', 'queria', 'quero', 'saber', 'informacoes', 'info', 'axixa',
    'tem', 'tinha', 'existe', 'ha', 'algum', 'alguma', 'uns', 'umas', 'um', 'uma',
    'banho', 'tomar', 'ir', 'chegar', 'encontrar', 'loja', 'lojas', 'municipal'
}

def safe_get(item, *keys):
    for key in keys:
        val = item.get(key) or item.get(key + " ")
        if val:
            return val
    return ""

def find_item_by_name(pergunta_lower: str, data: dict):
    if not data or not pergunta_lower:
        return None, None

    pergunta_limpa = normalize_text(pergunta_lower)
    
    pergunta_keywords = {
        word for word in pergunta_limpa.split() if word not in STOP_WORDS and len(word) > 2
    }
    
    if not pergunta_keywords:
        return None, None

    lists_to_search = ["pontos_turisticos", "igrejas", "lojas", "escolas", "predios_municipais", "campos_esportivos", "cemiterios", "pousadas_dormitorios"]
    
    found_item = None
    found_key = None
    best_match_score = 0

    for key in lists_to_search:
        for item in data.get(key, []):
            texto_item = safe_get(item, "nome", "orgao") + " " + \
                         safe_get(item, "localizacao", "endereco", "endereço") + " " + \
                         safe_get(item, "descricao", "descrição")
            
            search_text_limpo = normalize_text(texto_item)
            
            current_match_score = 0
            for keyword in pergunta_keywords:
                if keyword in search_text_limpo:
                    current_match_score += 1 
            
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
                "campos_esportivos": (["quadra", "campo", "ginasio", "estadio"], ["quadra", "campo", "ginasio", "estadio"]),
                "igrejas": (["igreja", "paroquia", "religiao"], ["igreja", "paroquia"]),
                "lojas": (["loja", "comprar", "mercado", "farmacia", "vende", "material", "materiais", "construcao", "moda", "calcados"], ["loja", "comprar", "mercado"]),
                "escolas": (["escola", "colegio", "estudar", "iema", "creche", "infancia"], ["escola", "colegio", "estudar"]),
                "predios_municipais": (["prefeitura", "secretaria", "cras", "camara", "vereador", "vereadores"], ["secretaria", "predio"]),
                "pontos_turisticos": (["turismo", "passear", "banho", "rio", "balneario", "praca"], ["turismo", "passear", "banho", "rio", "balneario"]),
                "cemiterios": (["cemiterio"], ["cemiterio"]),
                "pousadas_dormitorios": (["pousada", "hotel", "dormir"], ["pousada", "hotel"])
            }

            categoria_selecionada = None
            keywords_to_remove = []

            for chave_json, (gatilhos, remover) in regras_categoria.items():
                if any(g in pergunta_normalizada for g in gatilhos):
                    categoria_selecionada = chave_json
                    keywords_to_remove = remover
                    break
            
            if categoria_selecionada:
                dados_raw = prompt_data.get(categoria_selecionada, [])
                termos_busca = set(pergunta_normalizada.split()) - set(keywords_to_remove) - STOP_WORDS
                
                filtered_data = []
                if not termos_busca and categoria_selecionada == "predios_municipais":
                    termos_busca = {"prefeitura"}

                if termos_busca:
                    for item in dados_raw:
                        texto_busca = normalize_text(
                            safe_get(item, "nome", "orgao") + " " + 
                            safe_get(item, "localizacao", "endereco", "endereço") + " " +
                            safe_get(item, "descricao", "descrição")
                        )
                        if any(t in texto_busca for t in termos_busca):
                            filtered_data.append(item)
                
                if len(filtered_data) > 1:
                    prioritarios = []
                    for item in filtered_data:
                        nome_orgao = normalize_text(safe_get(item, "nome", "orgao"))
                        if any(t in nome_orgao for t in termos_busca):
                            prioritarios.append(item)
                    
                    if len(prioritarios) > 0:
                        filtered_data = prioritarios

                if filtered_data:
                    item_encontrado = filtered_data[0]
                    item_data_json = json.dumps(filtered_data, ensure_ascii=False)

            if not item_data_json:
                item_encontrado, _ = find_item_by_name(pergunta_lower, prompt_data)
                if item_encontrado:
                    item_data_json = json.dumps(item_encontrado, ensure_ascii=False)

    if item_encontrado: 
        local_nome = safe_get(item_encontrado, "nome", "orgao")
        endereco = safe_get(item_encontrado, "localizacao", "endereco", "endereço")
        
        query_mapa = local_nome
        if endereco and endereco.lower() not in ["centro", "zona rural"]:
            query_mapa = f"{local_nome}, {endereco}"
        mapa_link = create_search_map_link(query_mapa)
    
    resposta_ia = conversar_com_guia(pergunta, system_prompt, item_data_json)

    return jsonify({"resposta": resposta_ia, "mapa_link": mapa_link, "local_nome": local_nome})

if __name__ == "__main__":
    app.run(debug=True)
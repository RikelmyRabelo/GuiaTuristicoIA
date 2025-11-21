import requests
import os
import json
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
import urllib.parse
import re
import unicodedata
from rapidfuzz import process, fuzz, utils

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
    """Remove acentos, caracteres especiais e converte para minúsculas."""
    if not text: return ""
    text = text.lower()
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s]', ' ', text)
    return text.strip()

def find_item_smart(pergunta: str, data: dict):
    if not data or not pergunta:
        return None

    pergunta_limpa = normalize_text(pergunta)
    
    stop_words = {
        'a', 'o', 'e', 'ou', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 
        'nos', 'nas', 'por', 'para', 'com', 'sem', 'sob', 'sobre', 
        'me', 'fale', 'diga', 'onde', 'fica', 'localiza', 'localizacao', 'qual', 'quais', 'sao', 'sou',
        'gostaria', 'queria', 'saber', 'informacoes', 'info', 'axixa', 'cidade', 'municipio',
        'ola', 'oi', 'como', 'faco', 'pra', 'chegar', 'quero',
        'tem', 'tinha', 'existe', 'ha', 'que', 'alguma', 'algum', 'uns', 'umas',
        'bairro', 'rua', 'av', 'avenida', 'povoado'
    }
    
    termos_importantes = [word for word in pergunta_limpa.split() if word not in stop_words and len(word) > 1]
    
    if not termos_importantes:
        query_final = pergunta_limpa
    else:
        query_final = " ".join(termos_importantes)

    category_keywords_map = {
        "escolas": ["escola", "colegio", "creche", "estudar", "ensino", "infancia", "fundamental", "medio", "educacao", "unidade"],
        "lojas": ["loja", "comprar", "mercado", "vende", "roupa", "moda", "moveis", "eletro", "calcados", "flor", "variedade", "material", "construcao", "floricultura", "mercadinho", "farmacia", "conveniencia", "distribuidora"],
        "pontos_turisticos": ["turismo", "passear", "banho", "rio", "praca", "igreja", "visitar", "ruina", "lazer", "turistico", "historico", "balneario"],
        "igrejas": ["igreja", "paroquia", "culto", "missa", "evangelica", "catolica", "assembleia", "batista"],
        "predios_municipais": ["prefeitura", "secretaria", "cras", "camara", "orgao", "publico", "saude", "assistencia"],
        "campos_esportivos": ["campo", "futebol", "ginasio", "jogo", "esporte", "quadra", "bola"],
        "cemiterios": ["cemiterio", "sepultamento", "enterrar"],
        "pousadas_dormitorios": ["pousada", "dormir", "hotel", "hospedagem", "quarto", "dormitorio"],
        "comidas_tipicas": ["comida", "tipica", "prato", "fome", "comer", "restaurante", "gastronomia", "culinaria", "almoco", "jantar", "peixe", "jucara"]
    }

    categorias_alvo = [
        "pontos_turisticos", "escolas", "lojas", "predios_municipais", 
        "igrejas", "campos_esportivos", "cemiterios", "pousadas_dormitorios", 
        "comidas_tipicas"
    ]

    best_item = None
    best_score = 0

    for categoria in categorias_alvo:
        cat_bonus = 0
        keywords = category_keywords_map.get(categoria, [])
        if any(kw in query_final for kw in keywords):
            cat_bonus = 15

        items = data.get(categoria, [])
        
        candidatos_texto = []
        candidatos_obj = []
        
        for item in items:
            nome = item.get("nome") or item.get("orgao") or ""
            local = item.get("localizacao") or item.get("endereco") or ""
            desc = item.get("descricao") or item.get("descrição") or ""
            
            texto_cru = f"{nome} {desc} {local} {categoria}"
            texto_busca = normalize_text(texto_cru)
            
            candidatos_texto.append(texto_busca)
            candidatos_obj.append(item)
            
        if not candidatos_texto:
            continue

        match = process.extractOne(query_final, candidatos_texto, scorer=fuzz.token_set_ratio)
        
        if match:
            score_base = match[1]
            score_final = score_base + cat_bonus
            
            item_match = candidatos_obj[match[2]]
            nome_item = normalize_text(item_match.get("nome") or item_match.get("orgao") or "")
            if fuzz.partial_ratio(query_final, nome_item) > 90:
                score_final += 10

            if score_final > best_score:
                best_score = score_final
                best_item = item_match

    if best_score >= 65:
        return best_item

    return None

def create_search_map_link(query: str) -> str:
    # CORREÇÃO: Link padrão do Google Maps Search
    full_query = f"{query}, Axixá, Maranhão"
    encoded_query = urllib.parse.quote(full_query)
    return f"https://www.google.com/maps/search/?api=1&query={encoded_query}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    pergunta = data.get("pergunta", "")
    pergunta_lower = pergunta.lower()

    if not pergunta:
        return jsonify({"erro": "Nenhuma pergunta fornecida."}), 400

    item_encontrado = None
    mapa_link = None
    local_nome = None
    item_data_json = None
    
    if prompt_data:
        texto_input = normalize_text(pergunta_lower)
        
        # 0. SAUDAÇÕES
        palavras_input = texto_input.split()
        saudacoes_keywords = ["ola", "oi", "opa", "salve", "eai", "hello"]
        frases_saudacao = ["bom dia", "boa tarde", "boa noite", "tude bem", "tudo bom"]
        
        is_saudacao = any(s in palavras_input for s in saudacoes_keywords) or \
                      any(f in texto_input for f in frases_saudacao)

        if is_saudacao:
             resposta_saudacao = (
                 "Olá! Sou o Guia Digital de Axixá. "
                 "Estou aqui para te ajudar a encontrar escolas, lojas, pontos turísticos, "
                 "órgãos públicos e conhecer a história da cidade. Como posso ajudar?"
             )
             return jsonify({"resposta": resposta_saudacao, "mapa_link": None, "local_nome": "Saudação"})

        # 1. Quem Fez
        criador_keywords = ["quem fez", "quem criou", "quem desenvolveu", "criador", "desenvolvedor", "quem e voce"]
        if any(phrase in texto_input for phrase in criador_keywords):
             resposta_criador = (
                 "Sou o Guia Digital - LocalizAxixá, desenvolvido por:\n\n"
                 "**Guilherme Moreira Santos**\n"
                 "**José Ribamar Andrade Santos Júnior**\n"
                 "**Marina de Jesus Lima Muniz**\n"
                 "**Rikelmy Rabelo Freitas**\n\n"
                 "Estou aqui para ajudar com informações sobre a cidade!"
             )
             return jsonify({"resposta": resposta_criador, "mapa_link": None, "local_nome": "Info dos Criadores"})

        # 2. História
        historia_keywords = ["historia", "fundacao", "origem", "emancipacao", "fundou", "criou", "economia", "cultura", "bumba"]
        if any(word in texto_input for word in historia_keywords):
            historia_data = prompt_data.get("historia_axixa")
            if historia_data:
                item_data_json = json.dumps(historia_data, ensure_ascii=False)
        
        # 3. Comidas
        elif "comida" in pergunta_lower or "prato" in pergunta_lower:
            if any(x in pergunta_lower for x in ["quais", "lista", "todas", "tipos", "sao"]):
                 comidas = prompt_data.get("comidas_tipicas", [])
                 if comidas:
                     item_data_json = json.dumps(comidas, ensure_ascii=False)
            else:
                item_encontrado = find_item_smart(pergunta, prompt_data)

        # 4. Busca Padrão
        else:
            item_encontrado = find_item_smart(pergunta, prompt_data)
    
    if item_encontrado and not item_data_json: 
        item_data_json = json.dumps(item_encontrado, ensure_ascii=False)
        local_nome = item_encontrado.get("nome") or item_encontrado.get("orgao")
        endereco = item_encontrado.get("localizacao") or item_encontrado.get("endereco")
        
        query_mapa = local_nome
        ignorar_mapa = ["zona rural", "vários locais", "região", "centro"]
        if endereco and not any(x in endereco.lower() for x in ignorar_mapa if len(endereco) < 10):
            query_mapa = f"{local_nome}, {endereco}"
        mapa_link = create_search_map_link(query_mapa)
    
    if not system_prompt:
        return jsonify({"erro": "Prompt do sistema não carregado no servidor."}), 500
    
    resposta_ia = conversar_com_chat(pergunta, system_prompt, item_data_json)

    return jsonify({"resposta": resposta_ia, "mapa_link": mapa_link, "local_nome": local_nome})

if __name__ == "__main__":
    app.run(debug=True)
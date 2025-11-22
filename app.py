import requests
import os
import json
import datetime
import threading  
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
import urllib.parse
import re
import unicodedata
from rapidfuzz import process, fuzz, utils
from supabase import create_client, Client
from constants import CATEGORIAS_ALVO, CATEGORY_KEYWORDS_MAP, STOP_WORDS

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-chat"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def log_interaction(pergunta, resposta, local_encontrado):
    """
    Esta função agora rodará em uma thread separada, 
    não bloqueando a resposta do usuário.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n--- LOG ASSÍNCRONO [{timestamp}] ---")
    print(f"User: {pergunta}")
    print(f"Local: {local_encontrado}")

    if SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            data = {
                "pergunta": pergunta,
                "resposta": resposta[:1000],
                "local": local_encontrado or "Nenhum"
            }
            
            supabase.table("logs").insert(data).execute()
            print("✅ Salvo no Supabase (Background)!")
            
        except Exception as e:
            print(f"Erro Supabase: {e}")
    else:
        print("Supabase não configurado.")

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
PROMPT_FILE = os.path.join(APP_ROOT, "prompt.json")

app = Flask(__name__)

SEARCH_CACHE = {}

def load_prompt_data(file_path: str) -> dict:
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"[Erro] Ocorreu um erro ao ler o {file_path}: {e}")
        return None

def normalize_text(text: str) -> str:
    if not text: return ""
    text = text.lower()
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s]', ' ', text)
    return text.strip()

def build_search_index(data: dict):
    global SEARCH_CACHE
    if not data: return
    
    for categoria in CATEGORIAS_ALVO:
        items = data.get(categoria, [])
        processed_texts = []
        processed_objects = []

        for item in items:
            nome = item.get("nome") or item.get("orgao") or ""
            local = item.get("localizacao") or item.get("endereco") or ""
            desc = item.get("descricao") or item.get("descrição") or ""
            
            texto_cru = f"{nome} {desc} {local} {categoria}"
            texto_busca = normalize_text(texto_cru)
            
            item["_nome_normalizado"] = normalize_text(nome)
            
            processed_texts.append(texto_busca)
            processed_objects.append(item)
        
        SEARCH_CACHE[categoria] = {
            "texts": processed_texts,
            "objects": processed_objects
        }

prompt_data = load_prompt_data(PROMPT_FILE)
 
if prompt_data:
    system_prompt = "\n".join(prompt_data.get("system_prompt", []))
    build_search_index(prompt_data)
else:
    system_prompt = None

def conversar_com_chat(pergunta: str, system_prompt: str, item_data_json: str = None, historico: list = None):
    if not system_prompt:
        return "[Erro crítico: O prompt do sistema não foi carregado.]"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https.seu-site-ou-projeto.com",
        "X-Title": "Guia Digital - LocalizAxixá",
    }
    
    messages = [{"role": "system", "content": system_prompt}]
    
    if historico:
        messages.extend(historico[-4:])
    
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

def find_item_smart(pergunta: str):
    if not pergunta:
        return None

    pergunta_limpa = normalize_text(pergunta)
    
    termos_importantes = [word for word in pergunta_limpa.split() if word not in STOP_WORDS and len(word) > 1]
    
    if not termos_importantes:
        query_final = pergunta_limpa
    else:
        query_final = " ".join(termos_importantes)

    best_item = None
    best_score = 0

    for categoria in CATEGORIAS_ALVO:
        cat_bonus = 0
        keywords = CATEGORY_KEYWORDS_MAP.get(categoria, [])
        if any(kw in query_final for kw in keywords):
            cat_bonus = 15

        cache_data = SEARCH_CACHE.get(categoria)
        if not cache_data or not cache_data["texts"]:
            continue
            
        candidatos_texto = cache_data["texts"]
        candidatos_obj = cache_data["objects"]
        
        match = process.extractOne(query_final, candidatos_texto, scorer=fuzz.token_set_ratio)
        
        if match:
            texto_match, score_base, index = match
            score_final = score_base + cat_bonus
            
            item_match = candidatos_obj[index]
            nome_norm = item_match.get("_nome_normalizado", "")
            
            if fuzz.partial_ratio(query_final, nome_norm) > 90:
                score_final += 10

            if score_final > best_score:
                best_score = score_final
                best_item = item_match

    if best_score >= 65:
        return best_item

    return None

def create_search_map_link(query: str) -> str:
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
    historico = data.get("historico", [])
    pergunta_lower = pergunta.lower()

    if not pergunta:
        return jsonify({"erro": "Nenhuma pergunta fornecida."}), 400

    item_encontrado = None
    mapa_link = None
    local_nome = None
    item_data_json = None
    
    if prompt_data:
        texto_input = normalize_text(pergunta_lower)
        
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
             threading.Thread(target=log_interaction, args=(pergunta, resposta_saudacao, "Saudação")).start()
             return jsonify({"resposta": resposta_saudacao, "mapa_link": None, "local_nome": "Saudação"})

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
             threading.Thread(target=log_interaction, args=(pergunta, resposta_criador, "Info dos Criadores")).start()
             return jsonify({"resposta": resposta_criador, "mapa_link": None, "local_nome": "Info dos Criadores"})

        historia_keywords = ["historia", "fundacao", "origem", "emancipacao", "fundou", "criou", "economia", "cultura", "bumba"]
        if any(word in texto_input for word in historia_keywords):
            historia_data = prompt_data.get("historia_axixa")
            if historia_data:
                item_data_json = json.dumps(historia_data, ensure_ascii=False)
                local_nome = "Dados Históricos"
        
        elif "comida" in pergunta_lower or "prato" in pergunta_lower:
            if any(x in pergunta_lower for x in ["quais", "lista", "todas", "tipos", "sao"]):
                 comidas = prompt_data.get("comidas_tipicas", [])
                 if comidas:
                     item_data_json = json.dumps(comidas, ensure_ascii=False)
                     local_nome = "Lista de Comidas"
            else:
                item_encontrado = find_item_smart(pergunta)

        else:
            item_encontrado = find_item_smart(pergunta)
    
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
    
    resposta_ia = conversar_com_chat(pergunta, system_prompt, item_data_json, historico)

    threading.Thread(target=log_interaction, args=(pergunta, resposta_ia, local_nome)).start()

    return jsonify({"resposta": resposta_ia, "mapa_link": mapa_link, "local_nome": local_nome})

if __name__ == "__main__":
    app.run(debug=True)
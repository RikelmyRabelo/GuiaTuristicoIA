import requests
import os
import json
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
import urllib.parse

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

def conversar_com_valdir(pergunta: str, system_prompt: str):
    
    if not system_prompt:
        return "[Erro crítico: O prompt do sistema não foi carregado.]"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://seu-site-ou-projeto.com",
        "X-Title": "Guia Digital Valdir Moraes",
    }

    payload = {
        "model": MODEL_NAME,
        "messages": 
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": pergunta}
        ],
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

def find_location_details(location_name: str, data: dict) -> str:
    if not data:
        return None
    
    list_keys = ["escolas", "lojas", "pontos_turisticos", "predios_municipais", "igrejas", "campos_esportivos"]
    
    for key in list_keys:
        for item in data.get(key, []):
            nome_local = item.get("nome", "").lower() or item.get("orgao", "").lower()
            if location_name.lower() in nome_local:
                if "localizacao" in item:
                    return item["localizacao"]
                if "endereco" in item:
                    return item["endereco"]
    return None

def create_search_map_link(query: str) -> str:
    full_query = f"{query}, Axixá, Maranhão"
    encoded_query = urllib.parse.quote(full_query)
    return f"https://www.google.com/maps/search/?api=1&query={encoded_query}"

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    
    if not system_prompt:
        return jsonify({"erro": "Prompt do sistema não carregado no servidor."}), 500

    data = request.json
    pergunta = data.get("pergunta")
    pergunta_lower = pergunta.lower() if pergunta else ""

    if not pergunta:
        return jsonify({"erro": "Nenhuma pergunta fornecida."}), 400

    resposta_ia = conversar_com_valdir(pergunta, system_prompt)
    
    mapa_link = None
    local_nome = None
    
    triggers_mapa = ["onde fica", "como chegar", "mapa", "localização", "ir para", "endereço de"]
    if any(trigger in pergunta_lower for trigger in triggers_mapa):
        
        location_name_found = None
        if prompt_data:
            all_items = []
            list_keys = ["escolas", "lojas", "pontos_turisticos", "predios_municipais", "igrejas", "campos_esportivos"]
            for key in list_keys:
                all_items.extend(prompt_data.get(key, []))
            
            for item in all_items:
                nome = item.get("nome") or item.get("orgao")
                if nome:
                    nome_simplificado = nome.split('(')[0].strip().lower()
                    if nome_simplificado and nome_simplificado in pergunta_lower: 
                        location_name_found = nome
                        break 
        
        if location_name_found:
            endereco = find_location_details(location_name_found, prompt_data)
            local_nome = location_name_found 
            
            query_mapa = location_name_found
            if endereco:
                query_mapa = f"{location_name_found}, {endereco}"
                
            mapa_link = create_search_map_link(query_mapa)

    return jsonify({"resposta": resposta_ia, "mapa_link": mapa_link, "local_nome": local_nome})

if __name__ == "__main__":
    if not OPENROUTER_API_KEY:
        print("Erro Crítico ")
        print("A variável OPENROUTER_API_KEY não foi encontrada.")
        print("Por favor, crie um arquivo .env e adicione sua chave nele.")
        print("Exemplo: OPENROUTER_API_KEY='sua-chave-aqui'")
    else:
        app.run(debug=True, port=5000)
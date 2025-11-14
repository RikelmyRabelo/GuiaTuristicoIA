import requests
import os
import json
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
import urllib.parse
import random

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
        "max_tokens": 500
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

def get_intro_message(category_key: str) -> str:
    messages = {
        "pontos_turisticos": [
            "Ótima escolha! Aqui estão os detalhes sobre esse ponto turístico:",
            "Claro, aqui está o que sei sobre esse lugar tão interessante:",
            "Ah, um belo local! Deixe-me ver o que tenho aqui sobre ele:"
        ],
        "igrejas": [
            "Um local de muita fé. Aqui estão as informações:",
            "Claro, aqui estão os detalhes sobre esta igreja:",
            "Sim, conheço. Aqui está o que você precisa saber:"
        ],
        "lojas": [
            "Boas compras! Aqui estão os detalhes desta loja:",
            "Procurando algo? Aqui estão as informações do local:",
            "Anotado. Aqui estão os detalhes:"
        ],
        "escolas": [
            "Informação importante. Aqui estão os dados da escola:",
            "Claro, aqui estão os detalhes da instituição de ensino:",
            "Sim, aqui está o que encontrei sobre esta escola:"
        ],
        "predios_municipais": [
            "Sim, claro. Aqui estão as informações do órgão municipal:",
            "Aqui estão os dados do prédio público que você pediu:"
        ],
        "campos_esportivos": [
            "Hora do jogo! Aqui estão os detalhes do campo:",
            "Claro, aqui estão as informações sobre o local esportivo:"
        ],
        "default": [
            "Claro, meu amigo. Aqui estão os detalhes que encontrei:",
            "Sim, aqui está o que você precisa saber:",
            "Anotado. Aqui estão as informações:"
        ]
    }
    
    message_list = messages.get(category_key, messages["default"])
    return random.choice(message_list)

def find_item_by_name(pergunta_lower: str, data: dict):
    if not data or not pergunta_lower:
        return None, None

    pergunta_limpa = pergunta_lower.replace("?", "").replace(".", "").replace("!", "").replace(",", "")

    lists_to_search = ["pontos_turisticos", "igrejas", "lojas", "escolas", "predios_municipais", "campos_esportivos"]

    for key in lists_to_search:
        for item in data.get(key, []):
            nome_completo = (item.get("nome", "") or item.get("orgao", "")).lower()
            if not nome_completo:
                continue

            nome_simplificado = nome_completo.split('(')[0].strip().lower()

            if (nome_simplificado and nome_simplificado in pergunta_limpa) or \
               (nome_completo in pergunta_limpa):
                return item, key

    return None, None

def format_item_response(item: dict) -> str:
    if not item:
        return "Não encontrei detalhes para este local."

    nome = item.get("nome") or item.get("orgao")
    response_lines = [f"**Nome:** {nome}"]

    endereco = item.get("localizacao") or item.get("endereco")
    if endereco:
        response_lines.append(f"**Endereço:** {endereco}")

    telefone = item.get("telefone")
    if telefone:
        response_lines.append(f"**Telefone:** {telefone}")
    else:
        response_lines.append(f"**Telefone:** Não tenho essa informação confirmada.")

    descricao = item.get("descricao")
    if descricao:
        response_lines.append(f"**Descrição:** {descricao}")

    dica = item.get("dica")
    if dica:
        response_lines.append(f"**Dica útil:** {dica}")

    return "\n\n".join(response_lines)

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
    
    data = request.json
    pergunta = data.get("pergunta")
    pergunta_lower = pergunta.lower() if pergunta else ""

    if not pergunta:
        return jsonify({"erro": "Nenhuma pergunta fornecida."}), 400

    item_encontrado, category_key = find_item_by_name(pergunta_lower, prompt_data)
    
    resposta_final = None
    mapa_link = None
    local_nome = None

    if item_encontrado:
        intro_message = get_intro_message(category_key)
        item_details = format_item_response(item_encontrado)
        
        resposta_final = f"{intro_message}\n\n{item_details}"
        
        local_nome = item_encontrado.get("nome") or item_encontrado.get("orgao")
        endereco = item_encontrado.get("localizacao") or item_encontrado.get("endereco")
        query_mapa = local_nome
        if endereco:
            query_mapa = f"{local_nome}, {endereco}"
        mapa_link = create_search_map_link(query_mapa)
    
    else:
        if not system_prompt:
            return jsonify({"erro": "Prompt do sistema não carregado no servidor."}), 500
        resposta_final = conversar_com_valdir(pergunta, system_prompt)

    return jsonify({"resposta": resposta_final, "mapa_link": mapa_link, "local_nome": local_nome})

if __name__ == "__main__":
    if not OPENROUTER_API_KEY:
        print("Erro Crítico ")
        print("A variável OPENROUTER_API_KEY não foi encontrada.")
        print("Por favor, crie um arquivo .env e adicione sua chave nele.")
        print("Exemplo: OPENROUTER_API_KEY='sua-chave-aqui'")
    else:
        app.run(debug=True, port=5000)
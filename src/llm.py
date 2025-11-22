import requests
from src.config import OPENROUTER_API_KEY, OPENROUTER_API_URL, MODEL_NAME

def conversar_com_chat(pergunta: str, system_prompt: str, item_data_json: str = None, historico: list = None):
    if not system_prompt: return "[Erro crítico: Prompt não carregado.]"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https.guialocalizaxixa.com",
        "X-Title": "Guia Digital - LocalizAxixá",
    }
    
    messages = [{"role": "system", "content": system_prompt}]
    if historico: messages.extend(historico[-4:])
    
    if item_data_json:
        messages.append({
            "role": "system", 
            "content": f"INSTRUÇÃO: Responda naturalmente usando *apenas* estes DADOS FACTUAIS: {item_data_json}"
        })
    
    messages.append({"role": "user", "content": pergunta})

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json={
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1024
        })
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Erro IA: {e}]"
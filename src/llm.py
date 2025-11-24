import requests
import json
from src.config import OPENROUTER_API_KEY, OPENROUTER_API_URL, MODEL_NAME

def conversar_com_chat(pergunta: str, system_prompt: str, item_data_json: str = None, historico: list = None):
    if not system_prompt:
        yield "[Erro crítico: Prompt não carregado.]"
        return

    # Headers corrigidos
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://guialocalizaxixa.com", # Corrigido typo
        "X-Title": "Guia Digital - LocalizAxixá",
    }
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Adiciona histórico se existir (últimos 4)
    if historico:
        messages.extend(historico[-4:])
    
    # Injeção de contexto (RAG)
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
            "max_tokens": 1024,
            "stream": True
        }, stream=True)
        
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8').replace('data: ', '').strip()
                if decoded_line and decoded_line != '[DONE]':
                    try:
                        json_line = json.loads(decoded_line)
                        content = json_line["choices"][0].get("delta", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        yield f"[Erro IA: {str(e)}]"
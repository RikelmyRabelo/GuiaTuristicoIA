import requests
import os
import json
from dotenv import load_dotenv


load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-chat"
PROMPT_FILE = "prompt.json" 


def load_system_prompt(file_path: str) -> str:
    """Carrega o prompt do sistema de um arquivo JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        prompt_lines = data["system_prompt"]
        
        return "\n".join(prompt_lines)
    
    except FileNotFoundError:
        print(f"[Erro] Arquivo de prompt não encontrado: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"[Erro] O arquivo {file_path} não é um JSON válido.")
        return None
    except KeyError:
        print(f"[Erro] Chave 'system_prompt' não encontrada no {file_path}.")
        return None
    except TypeError:
        print(f"[Erro] O valor de 'system_prompt' no JSON não é uma lista de strings.")
        return None
    except Exception as e:
        print(f"[Erro] Ocorreu um erro ao ler o prompt: {e}")
        return None

def conversar_com_valdir(pergunta: str, system_prompt: str):
    """Envia a pergunta para a API OpenRouter com o prompt de sistema."""
    
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
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": pergunta}
        ],
        "temperature": 0.7,
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

def main():
    """Função principal que executa o loop do chat."""
    
    if not OPENROUTER_API_KEY:
        print("🚨 [Erro Crítico] 🚨")
        print("A variável OPENROUTER_API_KEY não foi encontrada.")
        print("Por favor, crie um arquivo .env e adicione sua chave nele.")
        print("Exemplo: OPENROUTER_API_KEY='sua-chave-aqui'")
        return

    system_prompt = load_system_prompt(PROMPT_FILE)
    if not system_prompt:
        return

    print("🤖 Guia Digital Valdir Moraes - Axixá do Maranhão 🌴\n")
    print("Dica: digite 'sair' para encerrar.\n")

    while True:
        pergunta = input("Você: ")
        if pergunta.lower() in ["sair", "exit", "tchau", "quit"]:
            print("Valdir: Até logo, meu amigo! Que Axixá o receba sempre bem. 👋")
            break
        
        resposta = conversar_com_valdir(pergunta, system_prompt)
        print("Valdir:", resposta)

if __name__ == "__main__":
    main()
import datetime
from supabase import create_client, Client
from src.config import SUPABASE_URL, SUPABASE_KEY

supabase_client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Erro ao conectar Supabase na inicialização: {e}")

def log_interaction(pergunta, resposta, local_encontrado):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n--- LOG [{timestamp}] ---")
    print(f"User: {pergunta}")
    print(f"Local: {local_encontrado}")

    if supabase_client:
        try:
            data = {
                "pergunta": pergunta,
                "resposta": resposta[:1000],
                "local": str(local_encontrado) or "Nenhum"
            }
            # Se falhar por permissão RLS ou rede, capturamos no except
            supabase_client.table("logs").insert(data).execute()
            print("Salvo no Supabase (Background)!")
        except Exception as e:
            print(f"Aviso Supabase (Log não salvo): {e}")
    else:
        print("Supabase não configurado ou indisponível.")
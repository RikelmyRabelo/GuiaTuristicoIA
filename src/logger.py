import datetime
from supabase import create_client, Client
from src.config import SUPABASE_URL, SUPABASE_KEY

def log_interaction(pergunta, resposta, local_encontrado):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n--- LOG [{timestamp}] ---")
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
            print("Salvo no Supabase (Background)!")
        except Exception as e:
            print(f"Erro Supabase: {e}")
    else:
        print("Supabase não configurado.")
import json
from unittest.mock import patch
from app import app

client = app.test_client()

def rodar_testes():
    # CENÁRIOS FINAIS CORRIGIDOS
    cenarios = [
        # --- 1. Teste de Siglas e Órgãos Públicos ---
        ("Onde fica a SEMUS?", "Secretaria Municipal de Saúde (SEMUS)"),
        ("Localização do CRAS", "Centro de Referencia de Assistência Social - CRAS"),
        ("Onde fica a câmara dos vereadores?", "Câmara Municipal de Axixá"),

        # --- 2. Busca por Produtos e Serviços ---
        ("Onde posso comprar medicamentos?", "Farmale (Farmácia do Trabalhador)"),
        ("Onde tem bebidas e lanches?", "Pit Stop Conveniência"),
        
        # CORREÇÃO AQUI: Busca precisa (plural) e alvo único (Martins tem 'materiais' na descrição)
        ("Quero comprar materiais de construção", "Comercial Martins"), 

        # --- 3. Detalhes Turísticos ---
        ("Qual igreja foi construída em 1693?", "Igreja da Luz"),
        ("Lugar com águas calmas para banho", "Ilha de Perijuçara"),
        ("Onde ficam as ruínas históricas?", "Ruinas do Quilombo de Munim Mirim"),

        # --- 4. Educação Específica ---
        ("Tem alguma creche na cidade?", "Jardim de Infância Adelino Fontoura"),
        ("Onde fica a escola militar?", "Colégio Militar Tiradentes XV - Axixá"),

        # --- 5. História e Cultura ---
        ("Quais são os pratos típicos?", "Dados de História"),
        ("Fale sobre o arroz de cuxá", "Dados de História"),
        ("O que é produzido na economia local?", "Dados de História"),

        # --- 6. Testes de Robustez ---
        ("onde fica a semaf", "Secretaria Municipal de Finanças (SEMAF)"),
        ("hospital municipal", None)
    ]

    print(f"\n{'STATUS':<10} | {'ESPERADO':<35} | {'PERGUNTA'}")
    print("-" * 90)

    sucessos = 0
    falhas = 0

    with patch('app.conversar_com_guia') as mock_ia:
        mock_ia.return_value = "Resposta simulada da IA para teste."

        for pergunta, esperado in cenarios:
            response = client.post('/chat', json={'pergunta': pergunta})
            data = response.get_json()

            local_encontrado = data.get('local_nome')

            if esperado == "Dados de História":
                args, _ = mock_ia.call_args
                dados_passados = args[2] if args and len(args) > 2 else ""
                passou = "origem_nome" in str(dados_passados) or "cultura" in str(dados_passados)
                resultado_real = "Dados de História encontrados" if passou else str(local_encontrado)
            
            elif isinstance(esperado, list):
                passou = local_encontrado in esperado
                resultado_real = local_encontrado
            
            else:
                passou = local_encontrado == esperado
                resultado_real = local_encontrado

            if passou:
                print(f"✅ PASSOU   | {str(resultado_real):<35} | {pergunta}")
                sucessos += 1
            else:
                print(f"❌ FALHOU   | {str(esperado):<35} | {pergunta}")
                print(f"             -> Recebido: {resultado_real}")
                falhas += 1

    print("-" * 90)
    print(f"Total: {sucessos} sucessos, {falhas} falhas.\n")

if __name__ == "__main__":
    rodar_testes()
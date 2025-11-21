import json
from unittest.mock import patch
from app import app

client = app.test_client()

def rodar_testes():
    cenarios = [
        ("Quem fez a IA?", "Info dos Criadores"),

        ("Existe uma igreja de São Benedito?", "Resposta da IA (Sem Local)"), 
        ("Tem alguma pousada?", "Recanto Azeite Doce"), 
        ("Onde tomar banho de rio?", "Ilha de Perijuçara"), 
        ("Praça da cidade", "Praça e Igreja do Centro"), 

        ("Quais são as comidas típicas da cidade?", "Lista de Comidas"),

        ("Escola no povoado Munim Mirim", "UE José Ribamar Fontoura"), 
        ("Escola em Santa Rosa", ["Jardim de Infância Lilian Cortes Maciel Vieira", "IEMA - Unidade Plena de Axixá"]), 
        ("Loja de calçados", "Axixá Multimarcas"), 
        ("Escola no Vale Quem Tem", "UI Arcelino Rodrigues Tavares"), 
        ("Tem alguma creche na cidade?", "Jardim de Infância Adelino Fontoura"), 
        ("Onde compro móveis?", ["Eli Lojas", "Lunna Eletromóveis"]), 
        ("Onde fica a Josy Boutique?", "Josy Boutique"),
        ("Quero visitar a Igreja da Luz", "Igreja da Luz"),
        ("Onde fica a Prefeitura?", "Prefeitura Municipal de Axixá"),
    ]

    print(f"\n{'STATUS':<10} | {'ESPERADO':<35} | {'PERGUNTA'}")
    print("-" * 90)

    sucessos = 0
    falhas = 0

    with patch('app.conversar_com_chat') as mock_ia:
        mock_ia.return_value = "Resposta simulada da IA."

        for pergunta, esperado in cenarios:
            try:
                response = client.post('/chat', json={'pergunta': pergunta})
                data = response.get_json()
                local_encontrado = data.get('local_nome')
                
                passou = False
                resultado_real = local_encontrado

                if esperado == "Info dos Criadores":
                    resposta = data.get('resposta', '')
                    passou = "Guilherme" in resposta and "Rikelmy" in resposta
                    resultado_real = "Info dos Criadores" if passou else "Resposta incorreta"

                elif esperado == "Lista de Comidas":
                    args, _ = mock_ia.call_args
                    dados = args[2] if args and len(args) > 2 else ""
                    passou = "Juçara" in str(dados) and "Peixe Assado" in str(dados)
                    resultado_real = "Lista completa enviada" if passou else str(local_encontrado)

                elif esperado == "Resposta da IA (Sem Local)":
                    passou = local_encontrado is None
                    resultado_real = "Sem Local (OK)" if passou else local_encontrado

                elif isinstance(esperado, list):
                    passou = local_encontrado in esperado
                
                else:
                    passou = local_encontrado == esperado

                if passou:
                    print(f"✅ PASSOU   | {str(resultado_real)[:35]:<35} | {pergunta}")
                    sucessos += 1
                else:
                    print(f"❌ FALHOU   | {str(esperado)[:35]:<35} | {pergunta}")
                    print(f"             -> Recebido: {resultado_real}")
                    falhas += 1

            except Exception as e:
                print(f"❌ ERRO CRÍTICO no teste: {pergunta} -> {e}")
                falhas += 1

    print("-" * 90)
    print(f"Total: {sucessos} sucessos, {falhas} falhas.")
    print(f"Taxa de Sucesso: {int((sucessos / len(cenarios)) * 100)}%\n")

if __name__ == "__main__":
    rodar_testes()
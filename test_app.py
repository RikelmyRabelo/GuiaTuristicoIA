import json
from unittest.mock import patch
from app import app

client = app.test_client()

def rodar_testes():
    cenarios = [
        ("Onde fica a escola IEMA?", "IEMA - Unidade Plena de Axixá"),
        ("Quero saber sobre o colégio militar", "Colégio Militar Tiradentes XV - Axixá"),
        ("Onde fica a escola Estado do Acre?", "Centro de Ensino Estado do Acre"),
        ("Escola no povoado Munim Mirim", "UE José Ribamar Fontoura"),
        ("Onde estudar em tempo integral?", "IEMA - Unidade Plena de Axixá"),
        ("Escola no Vale Quem Tem", "UI Arcelino Rodrigues Tavares"),
        ("Tem alguma creche na cidade?", "Jardim de Infância Adelino Fontoura"),
        ("Tem alguma escola no povoado Burgos?", "Unidade Integrada Major Fontoura"),

    ]

    print(f"\n{'STATUS':<10} | {'ESPERADO':<35} | {'PERGUNTA'}")
    print("-" * 90)

    sucessos = 0
    falhas = 0

    with patch('app.conversar_com_guia') as mock_ia:
        mock_ia.return_value = "Resposta simulada da IA para teste."

        for pergunta, esperado in cenarios:
            try:
                response = client.post('/chat', json={'pergunta': pergunta})
                data = response.get_json()
                local_encontrado = data.get('local_nome')
                
                passou = False
                resultado_real = local_encontrado

                if esperado == "Dados de História":
                    args, _ = mock_ia.call_args
                    dados_passados = args[2] if args and len(args) > 2 else ""
                    tem_dados = any(k in str(dados_passados) for k in ["origem_nome", "economia", "cultura"])
                    passou = tem_dados
                    resultado_real = "Dados de História" if passou else str(local_encontrado)
                
                elif expected_is_list := isinstance(esperado, list):
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
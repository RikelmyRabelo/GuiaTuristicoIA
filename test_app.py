import json
from unittest.mock import patch
from app import app

client = app.test_client()

def rodar_testes():
    cenarios = [
        ("Onde fica a escola IEMA?", "IEMA - Unidade Plena de Axixá"),
        ("Quero saber sobre o colégio militar", "Colégio Militar Tiradentes XV - Axixá"),
        
        ("Onde compro roupas na Josy?", "Josy Boutique"),
        ("Tem alguma loja de móveis?", "Eli Lojas"),
        ("telefone do pit stop", "Pit Stop Conveniência"),

        ("Quero tomar banho no balneário santa vitória", "Balneario Santa Vitória"),
        ("Fale sobre a Igreja da Luz", "Igreja da Luz"),

        ("Qual a história de fundação de Axixá?", "historia_axixa"),

        ("Onde fica a prefeitura?", "Prefeitura Municipal de Axixá"),
        
        ("Onde tem um posto de gasolina?", None) 
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

            if esperado == "historia_axixa":
                args, _ = mock_ia.call_args
                dados_passados = args[2] if len(args) > 2 else ""
                passou = "origem_nome" in str(dados_passados)
                resultado_real = "Dados de História" if passou else "Nenhum dado"
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
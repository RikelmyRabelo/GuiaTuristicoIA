import json
from unittest.mock import patch
from app import app

client = app.test_client()

def rodar_testes():
    cenarios = [
        ("Onde fica a escola IEMA?", "IEMA - Unidade Plena de Axixá"),
        ("Onde fica a Prefeitura?", "Prefeitura Municipal de Axixá"),
        ("Onde posso comprar flores?", "Nova Flor"),
        ("Quero comer galinha caipira", "Restaurante da Mocinha"),
        ("Onde comprar móveis e decoração?", ["Eli Lojas", "Lunna Eletromóveis"]),
        ("Tem alguma escola no povoado Burgos?", "Unidade Integrada Major Fontoura"),
        ("Igreja no bairro São Benedito", "Igreja Batista de Jesus Cristo"),
        ("Onde fica o ginásio de esportes?", "Ginásio Poliesportivo José Pedro Ferreira Reis"),
        ("Onde é o cemitério municipal?", "Cemitério Municipal de Axixá"),
        ("Quero dormir no recanto azeite doce", "Recanto Azeite Doce"),
        ("onde fica a paroquia nossa senhora da saude", "Paróquia Nossa Senhora da Saúde - Igreja Católica"),
        ("ruinas do quilombo", "Ruinas do Quilombo de Munim Mirim"),
        ("Fale sobre o Bumba Meu Boi da cidade", "Dados de História"),
        ("Quem fundou Axixá?", "Dados de História"),
        ("Onde tem um cinema?", None),
        ("Onde fica o aeroporto?", None)
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
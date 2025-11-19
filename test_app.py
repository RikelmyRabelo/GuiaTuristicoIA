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

        ("Onde compro roupas na Josy?", "Josy Boutique"),
        ("telefone do pit stop", "Pit Stop Conveniência"),
        ("Onde posso comprar flores?", "Nova Flor"),
        ("Onde comprar moda praia?", "La Vista"),
        ("Loja de variedades", "Axixá Variadades"),
        ("Onde comprar no atacado?", "N.C. Distribuidora"),
        ("Quero tomar açaí", "Juçara Açaí - Merão e Edite"),
        ("farmacia do trabalhador", "Farmale (Farmácia do Trabalhador)"),
        ("loja top 20", "Top20 Loja"),
        ("Onde posso comprar medicamentos?", "Farmale (Farmácia do Trabalhador)"),
        ("Onde tem bebidas e lanches?", "Pit Stop Conveniência"),
        ("Quero comprar materiais de construção", "Comercial Martins"),

        ("Loja de móveis", ["Eli Lojas", "Lunna Eletromóveis", "Mayra Magazine"]),
        ("Onde fica a Eli Lojas?", "Eli Lojas"),
        ("Onde comprar calçados?", ["Axixá Multimarcas", "Dany Multimarcas"]),

        ("Onde fica a prefeitura?", "Prefeitura Municipal de Axixá"),
        ("Telefone da SINFRA", "Secretaria Municipal de Infraestrutura (SINFRA)"),
        ("Onde fica a secretaria de agricultura?", "Secretaria Municipal de Agricultura e Abastecimento (SAP)"),
        ("Secretaria de Meio Ambiente", "Secretaria Municipal de Meio Ambiente"),
        ("Onde fica a secretaria de educação?", "Secretaria Municipal de Educação (SEMED)"),
        ("onde fica a semaf", "Secretaria Municipal de Finanças (SEMAF)"),
        ("Onde fica a SEMUS?", "Secretaria Municipal de Saúde (SEMUS)"),
        ("Localização do CRAS", "Centro de Referencia de Assistência Social - CRAS"),
        ("Onde fica a câmara dos vereadores?", "Câmara Municipal de Axixá"),

        ("Quero tomar banho no balneário santa vitória", "Balneario Santa Vitória"),
        ("Fale sobre a Igreja da Luz", "Igreja da Luz"),
        ("Qual igreja foi construída em 1693?", "Igreja da Luz"),
        ("Lugar com águas calmas para banho", "Ilha de Perijuçara"),
        ("Onde ficam as ruínas históricas?", "Ruinas do Quilombo de Munim Mirim"),
        ("ruinas do quilombo", "Ruinas do Quilombo de Munim Mirim"),
        ("Restaurante da Mocinha", "Restaurante da Mocinha"),
        ("Quero comer galinha caipira", "Restaurante da Mocinha"),
        ("Quero dormir no recanto azeite doce", "Recanto Azeite Doce"),

        ("Onde fica a assembleia de deus?", "Igreja Evangélica Assembleia de Deus"),
        ("Igreja no bairro São Benedito", "Igreja Batista de Jesus Cristo"),
        ("onde fica a paroquia nossa senhora da saude", "Paróquia Nossa Senhora da Saúde - Igreja Católica"),
        ("Onde fica a igreja matriz?", ["Paróquia Nossa Senhora da Saúde - Igreja Católica", "Praça e Igreja do Centro"]),
        ("Igreja no centro", ["Paróquia Nossa Senhora da Saúde - Igreja Católica", "Praça e Igreja do Centro"]),

        ("Onde fica o ginásio de esportes?", "Ginásio Poliesportivo José Pedro Ferreira Reis"),
        ("Campo de futebol do Riachão", "Campo do Riachão"),
        ("Onde fica o campo do bomfim?", "Campo do Bomfim"),
        ("Ginásio em Burgos", "Ginásio Poliesportivo - Burgos"),

        ("Onde é o cemitério municipal?", "Cemitério Municipal de Axixá"),
        ("Cemitério do Belém", "Cemitério do Belém"),
        ("Cemitério em Santa Rosa", "Cemitério do Cedro / Santa Rosa"),

        ("Qual a história de fundação de Axixá?", "Dados de História"),
        ("Qual a origem do nome da cidade?", "Dados de História"),
        ("Fale sobre o Bumba Meu Boi da cidade", "Dados de História"),
        ("Quem fundou Axixá?", "Dados de História"),
        ("Quais são os pratos típicos?", "Dados de História"),
        ("Fale sobre o arroz de cuxá", "Dados de História"),
        ("Como é a economia local?", "Dados de História"),

        ("Onde tem um posto de gasolina?", None),
        ("Onde tem um cinema?", None),
        ("Onde fica o aeroporto?", None),
        ("Tem shopping?", None),
        ("hospital municipal", None)
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
import json
import re
import unicodedata
from unittest.mock import patch
from app import app

client = app.test_client()

def normalizar_para_teste(text):
    """
    Remove acentos e coloca em minúsculas para comparar o esperado com o recebido.
    """
    if not isinstance(text, str): return str(text)
    text = text.lower()
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    return text.strip()

def rodar_testes():
    cenarios = [
        # --- NOVO: SAUDAÇÕES ---
        ("Olá, tudo bem?", "Saudação"),
        ("Oi guia", "Saudação"),
        ("Opa", "Saudação"),

        # --- PERGUNTAS ESPECÍFICAS SOLICITADAS ---
        ("Onde fica a igreja da luz?", "Igreja da Luz"),
        ("Quem desenvolveu você?", "Info dos Criadores"),
        ("Quais são as comidas típicas da cidade?", "Lista de Comidas"),

        # --- QUEM FEZ / SOBRE A IA ---
        ("Quem criou esse sistema?", "Info dos Criadores"),
        ("Quem é o desenvolvedor?", "Info dos Criadores"),

        # --- ESCOLAS (Zona Urbana e Rural) ---
        ("Onde fica a escola Major Fontoura?", "Unidade Integrada Major Fontoura"),
        ("Escola no povoado Perijuçara", "UI Professor Manoel Santana Baldez"),
        ("Escola no Vale Quem Tem", "UI Arcelino Rodrigues Tavares"),
        ("Escola no Munim Mirim", "UE José Ribamar Fontoura"),
        ("Onde fica a escola Axixaense?", "UE Axixaense"),
        ("Onde fica o Centro de Ensino Estado do Acre?", "Centro de Ensino Estado do Acre"),
        ("Onde fica o IEMA?", "IEMA - Unidade Plena de Axixá"),
        ("Escola Felipe Barbosa", "Unidade Integrada Felipe Barbosa de Andrade"),
        ("Tem alguma creche?", "Jardim de Infância Adelino Fontoura"),
        ("Onde fica o Colégio Militar?", "Colégio Militar Tiradentes XV - Axixá"),
        ("Escola em Santa Rosa", ["Jardim de Infância Lilian Cortes Maciel Vieira", "IEMA - Unidade Plena de Axixá"]),
        ("Escola no Ruy Vaz", ["JI Professor Maximiano Santos Lima", "UE Axixaense"]),
        ("Escola Dr. Saturnino Belo", "UE Dr. Saturnino Belo"),
        ("Escola no povoado Belém", "UE Dr. Genesio Rego"),
        ("Escola no Bomfim", "UE Joaquim Silva"),
        ("Escola no Iguaperiba", "UE Professor Vicente Pires"),
        ("Escola no Riachão", "UI Senador Clodomir Cardoso"),
        ("Escola Maria Vitória", ["Unidade Mais Integrada Professora Maria Vitória Santos", "UE Maria Vitória Santos Marques"]),

        # --- LOJAS E COMÉRCIO ---
        ("Onde compro móveis?", ["Eli Lojas", "Mayra Magazine", "Lunna Eletromóveis"]),
        ("Loja de moda praia", "La Vista"),
        ("Onde fica a Josy Boutique?", "Josy Boutique"),
        ("Tem loja de variedades?", "Axixá Variadades"),
        ("Onde fica a Top20?", "Top20 Loja"),
        ("Loja de calçados", ["Axixá Multimarcas", "Dany Multimarcas"]),
        ("Floricultura na cidade", "Nova Flor"),
        ("Onde tem conveniência?", "Pit Stop Conveniência"),
        ("Tem farmácia na cidade?", ["Farmale", "Farmale (Farmácia do Trabalhador)"]),
        ("Mercadinho no Riachão", "Comercial Silva P. de Cássia"),
        ("Distribuidora de bebidas", "N.C. Distribuidora"),
        ("Material de construção ou mercado", "Comercial Martins"),

        # --- PONTOS TURÍSTICOS ---
        ("Onde tomar banho de rio?", "Ilha de Perijuçara"),
        ("Quero visitar a Igreja Matriz", "Praça e Igreja do Centro"),
        ("Onde fica o Balneário Santa Vitória?", "Balneário Santa Vitória"),
        ("Tem ruínas históricas?", "Ruínas do Quilombo de Munim Mirim"),
        ("Principal praça da cidade", "Praça e Igreja do Centro"),

        # --- HISTÓRIA (Contexto) ---
        ("Qual a origem do nome Axixá?", "Dados de História"),
        ("Quem fundou a cidade?", "Dados de História"),
        ("Quando foi a emancipação?", "Dados de História"),
        ("Fale sobre a cultura e o bumba meu boi", "Dados de História"),

        # --- PRÉDIOS MUNICIPAIS ---
        ("Onde fica a Prefeitura?", "Prefeitura Municipal de Axixá"),
        ("Onde fica a Secretaria de Educação?", "Secretaria Municipal de Educação (SEMED)"),
        ("Onde fica a Secretaria de Saúde?", "Secretaria Municipal de Saúde (SEMUS)"),
        ("Onde fica o CRAS?", ["CRAS - Centro de Referência de Assistência Social", "Centro de Referencia de Assistência Social - CRAS"]),

        # --- IGREJAS ---
        ("Onde fica a Assembleia de Deus?", "Igreja Evangélica Assembleia de Deus"),
        ("Igreja Batista", "Igreja Batista de Jesus Cristo"),
        ("Igreja Vale de Bênção", "Igreja Vale de Bênção (IBVB)"),
        # Teste negativo importante
        ("Existe uma igreja de São Benedito?", "Resposta da IA (Sem Local)"),

        # --- ESPORTES ---
        ("Onde tem estádio de futebol?", "Campo Municipal / Estádio"),
        ("Ginásio de esportes no centro", "Ginásio Poliesportivo José Pedro Ferreira Reis"),
        ("Campo de futebol no Riachão", "Campo do Riachão"),

        # --- CEMITÉRIOS ---
        ("Onde fica o cemitério municipal?", "Cemitério Municipal de Axixá"),
        ("Cemitério no povoado Riachão", "Cemitério do Riachão"),

        # --- HOSPEDAGEM ---
        ("Tem alguma pousada ou hotel?", "Recanto Azeite Doce"),
        ("Onde posso dormir?", "Recanto Azeite Doce"),
    ]

    print(f"\n{'STATUS':<10} | {'ESPERADO':<35} | {'PERGUNTA'}")
    print("-" * 100)

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

                # Validação para "Saudação"
                if esperado == "Saudação":
                    resposta = data.get('resposta', '')
                    passou = "Olá! Sou o Guia Digital de Axixá" in resposta
                    resultado_real = "Saudação Correta" if passou else "Resposta Incorreta"

                # Validação para "Quem Fez"
                elif esperado == "Info dos Criadores":
                    resposta = data.get('resposta', '')
                    passou = "Guilherme" in resposta and "Rikelmy" in resposta
                    resultado_real = "Info dos Criadores" if passou else "Resposta incorreta"

                # Validação para Lista de Comidas
                elif esperado == "Lista de Comidas":
                    args, _ = mock_ia.call_args
                    dados = args[2] if args and len(args) > 2 else ""
                    passou = "Juçara" in str(dados) and "Peixe Assado" in str(dados)
                    resultado_real = "Lista completa enviada" if passou else str(local_encontrado)

                # Validação para História
                elif esperado == "Dados de História":
                    args, _ = mock_ia.call_args
                    dados = args[2] if args and len(args) > 2 else ""
                    passou = "origem_nome" in str(dados)
                    resultado_real = "Dados de História" if passou else str(local_encontrado)

                # Validação para Sem Local (Teste Negativo)
                elif esperado == "Resposta da IA (Sem Local)":
                    passou = local_encontrado is None
                    resultado_real = "Sem Local (OK)" if passou else local_encontrado

                # Validação para Listas (quando mais de um local serve)
                elif isinstance(esperado, list):
                    loc_norm = normalizar_para_teste(local_encontrado)
                    lista_norm = [normalizar_para_teste(e) for e in esperado]
                    passou = any(loc_norm == item or item in loc_norm for item in lista_norm)
                
                # Validação Padrão (Nome exato)
                else:
                    loc_norm = normalizar_para_teste(local_encontrado)
                    esp_norm = normalizar_para_teste(esperado)
                    passou = (loc_norm == esp_norm) or (esp_norm in loc_norm) or (loc_norm in esp_norm)

                status_icon = "✅ PASSOU" if passou else "❌ FALHOU"
                print(f"{status_icon:<10} | {str(esperado)[:35]:<35} | {pergunta}")
                
                if passou:
                    sucessos += 1
                else:
                    print(f"             -> Recebido: {resultado_real}")
                    falhas += 1

            except Exception as e:
                print(f"❌ ERRO CRÍTICO no teste: {pergunta} -> {e}")
                falhas += 1

    print("-" * 100)
    print(f"Total de Testes: {len(cenarios)}")
    print(f"Sucessos: {sucessos}")
    print(f"Falhas:   {falhas}")
    
    if len(cenarios) > 0:
        taxa = int((sucessos / len(cenarios)) * 100)
        print(f"Taxa de Sucesso: {taxa}%")

if __name__ == "__main__":
    rodar_testes()
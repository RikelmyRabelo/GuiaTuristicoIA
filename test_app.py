import json
from unittest.mock import patch
from app import app

client = app.test_client()

def rodar_testes():
    # BATERIA DE TESTES COMPLETA (30+ Cenários)
    cenarios = [
        # === 1. ESCOLAS E EDUCAÇÃO (Nomes e Localidades) ===
        ("Onde fica a escola Estado do Acre?", "Centro de Ensino Estado do Acre"),
        ("Escola no povoado Munim Mirim", "UE José Ribamar Fontoura"),
        ("Onde estudar em tempo integral?", "IEMA - Unidade Plena de Axixá"), # Busca pela descrição
        ("Escola no Vale Quem Tem", "UI Arcelino Rodrigues Tavares"),
        
        # === 2. LOJAS E PRODUTOS (Descrições Específicas) ===
        ("Onde comprar moda praia?", "La Vista"), # Descrição: "moda praia"
        ("Loja de variedades", "Axixá Variadades"),
        ("Onde comprar no atacado?", "N.C. Distribuidora"), # Descrição: "atacado"
        ("Quero tomar açaí", "Juçara Açaí - Merão e Edite"),
        ("Onde comprar flores?", "Nova Flor"),
        
        # === 3. AMBIGUIDADE (Produtos vendidos em vários lugares) ===
        # Aceita qualquer uma das lojas que vendem calçados
        ("Onde comprar calçados?", ["Axixá Multimarcas", "Dany Multimarcas"]), 
        # Aceita qualquer uma das 3 lojas de móveis cadastradas
        ("Loja de móveis", ["Eli Lojas", "Lunna Eletromóveis", "Mayra Magazine"]), 

        # === 4. ÓRGÃOS PÚBLICOS E SIGLAS ===
        ("Telefone da SINFRA", "Secretaria Municipal de Infraestrutura (SINFRA)"),
        ("Onde fica a secretaria de agricultura?", "Secretaria Municipal de Agricultura e Abastecimento (SAP)"),
        ("Secretaria de Meio Ambiente", "Secretaria Municipal de Meio Ambiente"),
        ("Onde fica a secretaria de educação?", "Secretaria Municipal de Educação (SEMED)"),

        # === 5. RELIGIÃO E IGREJAS ===
        ("Onde fica a assembleia de deus?", "Igreja Evangélica Assembleia de Deus"),
        ("Igreja no centro", ["Paróquia Nossa Senhora da Saúde - Igreja Católica", "Igreja Evangélica Assembleia de Deus", "Igreja Vale de Bênção (IBVB)"]), # Várias no centro
        
        # === 6. ESPORTES E LAZER (Zona Rural e Urbana) ===
        ("Campo de futebol do Riachão", "Campo do Riachão"),
        ("Onde fica o campo do bomfim?", "Campo do Bomfim"),
        ("Ginásio em Burgos", "Ginásio Poliesportivo - Burgos"),

        # === 7. CEMITÉRIOS (Busca por Povoado) ===
        ("Cemitério do Belém", "Cemitério do Belém"),
        ("Cemitério em Santa Rosa", "Cemitério do Cedro / Santa Rosa"),

        # === 8. PONTOS TURÍSTICOS E HISTÓRIA ===
        ("Qual a origem do nome da cidade?", "Dados de História"),
        ("Como é a economia local?", "Dados de História"),
        ("Onde fica a igreja matriz?", "Praça e Igreja do Centro"), # Apelido comum para "Igreja do Centro"
        
        # === 9. TESTES DE ROBUSTEZ (Erros e Variações) ===
        ("farmacia do trabalhador", "Farmale (Farmácia do Trabalhador)"), # Nome parcial
        ("loja top 20", "Top20 Loja"), # Inversão de nome
        ("restaurante da mocinha", "Restaurante da Mocinha"),
        ("Onde fica o aeroporto?", None), # Negativo
        ("Tem shopping?", None) # Negativo
    ]

    print(f"\n{'STATUS':<10} | {'ESPERADO':<35} | {'PERGUNTA'}")
    print("-" * 90)

    sucessos = 0
    falhas = 0

    with patch('app.conversar_com_guia') as mock_ia:
        mock_ia.return_value = "Resposta simulada da IA."

        for pergunta, esperado in cenarios:
            response = client.post('/chat', json={'pergunta': pergunta})
            data = response.get_json()
            local_encontrado = data.get('local_nome')

            # Lógica de Validação
            if esperado == "Dados de História":
                args, _ = mock_ia.call_args
                dados_passados = args[2] if args and len(args) > 2 else ""
                # Verifica se campos de história foram passados
                passou = any(k in str(dados_passados) for k in ["origem_nome", "economia", "cultura"])
                resultado_real = "Dados de História" if passou else str(local_encontrado)
            
            elif isinstance(esperado, list):
                # Se o resultado estiver DENTRO da lista de esperados, passa
                passou = local_encontrado in esperado
                resultado_real = local_encontrado
            
            else:
                passou = local_encontrado == esperado
                resultado_real = local_encontrado

            # Print do Resultado
            if passou:
                print(f"✅ PASSOU   | {str(resultado_real)[:35]:<35} | {pergunta}")
                sucessos += 1
            else:
                print(f"❌ FALHOU   | {str(esperado)[:35]:<35} | {pergunta}")
                print(f"             -> Recebido: {resultado_real}")
                falhas += 1

    print("-" * 90)
    print(f"Total: {sucessos} sucessos, {falhas} falhas.\n")

if __name__ == "__main__":
    rodar_testes()
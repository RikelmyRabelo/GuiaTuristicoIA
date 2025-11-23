import sys
import os
import pytest
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, limiter

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['RATELIMIT_ENABLED'] = False
    limiter.enabled = False
    
    with patch('app.conversar_com_chat') as mock_chat:
        def side_effect(pergunta, system, item_data, hist):
            if item_data and "povoados" in str(item_data):
                return "A cidade é cheia de povoados. Aqui estão algumas opções..."
            return "Resposta simulada da IA."
        mock_chat.side_effect = side_effect
        
        with app.test_client() as client:
            yield client
    
    limiter.enabled = True

def post_pergunta(client, texto):
    response = client.post('/chat', json={'pergunta': texto})
    if response.status_code == 429:
        pytest.fail("Erro 429: Rate Limit ainda está ativo! O teste foi bloqueado.")
    
    data = response.get_json()
    if data is None:
        pytest.fail(f"Erro: API não retornou JSON. Status: {response.status_code}")
        
    return data

CENARIOS = [
    ("Olá", "Saudação"),
    ("Oi, tudo bem?", "Saudação"),
    ("Bom dia guia", "Saudação"),
    ("Boa tarde", "Saudação"),
    ("Boa noite", "Saudação"),
    ("Quem é você?", "Créditos"),
    ("Quem criou este sistema?", "Créditos"),
    ("Quem desenvolveu o bot?", "Créditos"),
    ("Fale sobre os criadores", "Créditos"),
    ("Quem sou eu?", "Créditos"),
    ("Onde fica o IEMA?", "IEMA - Unidade Plena de Axixá"),
    ("Escola Major Fontoura", "Unidade Integrada Major Fontoura"),
    ("Onde fica a escola Delarey?", "UI Delarey Cardoso Nunes"),
    ("Escola no povoado Perijuçara", "UI Professor Manoel Santana Baldez"),
    ("Escola no Vale Quem Tem", "UI Arcelino Rodrigues Tavares"),
    ("Onde fica a UE Axixaense?", "UE Axixaense"),
    ("Colégio Militar", "Colégio Militar Tiradentes XV - Axixá"),
    ("Tem escola no Munim Mirim?", "UE José Ribamar Fontoura"),
    ("Escola em Santa Rosa", ["UI Delarey Cardoso Nunes", "IEMA", "Geral"]),
    ("Jardim de Infância Adelino", "Jardim de Infância Adelino Fontoura"),
    ("Escola Dr. Saturnino Belo", "UE Dr. Saturnino Belo"),
    ("Escola Genesio Rego", "UE Dr. Genesio Rego"),
    ("Escola no Bomfim", "UE Joaquim Silva"),
    ("Escola em Iguaperiba", "UE Professor Vicente Pires"),
    ("Escola no Riachão", "UI Senador Clodomir Cardoso"),
    ("Escola no Cedro", "Unidade Integrada João Clímaco de Almeida"),
    ("Escola Maria Vitória", ["UE Maria Vitória Santos Marques", "Unidade Mais Integrada"]),
    ("Quero ver escolas", "Geral: escolas"),
    ("Quais as escolas da cidade?", "Geral: escolas"), 
    ("Onde estudar?", "Geral: escolas"),
    ("Onde fica a Eli Lojas?", "Eli Lojas"),
    ("Loja La Vista", "La Vista"),
    ("Onde comprar roupas?", ["Josy Boutique", "La Vista", "Top20", "Dany", "Axixá Multimarcas"]),
    ("Josy Boutique", "Josy Boutique"),
    ("Tem loja de variedades?", "Axixá Variadades"),
    ("Top20 Loja", "Top20 Loja"),
    ("Axixá Multimarcas", "Axixá Multimarcas"),
    ("Floricultura Nova Flor", "Nova Flor"),
    ("Pit Stop Conveniência", "Pit Stop Conveniência"),
    ("Mayra Magazine", "Mayra Magazine"),
    ("Tem farmácia?", "Farmale"),
    ("Comercial Silva", "Comercial Silva P. de Cássia"),
    ("Lunna Eletromóveis", "Lunna Eletromóveis"),
    ("Comercial Ferreira", "Comercial Ferreira"),
    ("Distribuidora de bebidas", "N.C. Distribuidora"),
    ("Comercial Martins", "Comercial Martins"),
    ("Loja10", "Loja10"),
    ("Dany Multimarcas", "Dany Multimarcas"),
    ("Quero ver lojas", "Geral: lojas"),
    ("Onde fazer compras?", "Geral: lojas"),
    ("Igreja da Luz", "Igreja da Luz"),
    ("Ilha de Perijuçara", "Ilha de Perijuçara"),
    ("Onde tomar banho de rio?", ["Ilha de Perijuçara", "Balneario Santa Vitória"]),
    ("Praça principal", "Praça e Igreja do Centro"),
    ("Igreja Matriz", "Praça e Igreja do Centro"),
    ("Balneário Santa Vitória", "Balneario Santa Vitória"),
    ("Tem ruínas na cidade?", "Ruinas do Quilombo de Munim Mirim"),
    ("Turismo em Axixá", "Geral: pontos_turisticos"), 
    ("Lazer na cidade", "Geral: pontos_turisticos"),
    ("Onde visitar?", "Geral: pontos_turisticos"),
    ("Tem praia?", ["Ilha de Perijuçara", "Geral"]), 
    ("Igreja antiga", ["Igreja da Luz", "Geral"]),
    ("Onde fica a Prefeitura?", "Prefeitura Municipal de Axixá"),
    ("Secretaria de Educação", "Secretaria Municipal de Educação (SEMED)"),
    ("Secretaria de Saúde", "Secretaria Municipal de Saúde (SEMUS)"),
    ("Onde fica o CRAS?", "Centro de Referencia de Assistência Social - CRAS"),
    ("Câmara Municipal", "Câmara Municipal de Axixá"),
    ("Secretaria de Finanças", ["Secretaria Municipal de Finanças", "SEMAF"]),
    ("Secretaria de Meio Ambiente", "Secretaria Municipal de Meio Ambiente"),
    ("Secretaria de Agricultura", "Secretaria Municipal de Agricultura e Abastecimento (SAP)"),
    ("Secretaria de Infraestrutura", "Secretaria Municipal de Infraestrutura (SINFRA)"),
    ("Quais os órgãos públicos?", "Geral: predios_municipais"),
    ("Igreja Assembleia de Deus", "Igreja Evangélica Assembleia de Deus"),
    ("Igreja Batista", "Igreja Batista de Jesus Cristo"),
    ("Igreja Vale de Bênção", "Igreja Vale de Bênção (IBVB)"),
    ("Tem igrejas na cidade?", "Geral: igrejas"),
    ("Paróquia Nossa Senhora da Saúde", "Paróquia Nossa Senhora da Saúde - Igreja Católica"),
    ("Estádio Municipal", "Campo Municipal / Estádio"),
    ("Ginásio José Pedro", "Ginásio Poliesportivo José Pedro Ferreira Reis"),
    ("Ginásio Santa Rosa", "Ginásio Poliesportivo Santa Rosa"),
    ("Campo do Riachão", "Campo do Riachão"),
    ("Campo do Perijuçara", "Campo do Perijuçara"),
    ("Campo da Rua da Sapucaia", "Campo da Rua da Sapucaia"),
    ("Campo do Bomfim", "Campo do Bomfim"),
    ("Campo do Vale Quem Tem", "Campo do Vale Quem Tem"),
    ("Onde praticar esportes?", "Geral: campos_esportivos"),
    ("Tem quadra de futebol?", ["Geral", "Campo"]),
    ("Onde dormir?", ["Recanto Azeite Doce", "Geral: pousadas_dormitorios"]),
    ("Pousada Azeite Doce", "Recanto Azeite Doce"),
    ("Onde comer?", "Geral: comidas_tipicas"),
    ("Pratos típicos", ["Comidas Típicas", "Geral"]),
    ("História da cidade", "História"),
    ("Onde fica o Shopping Center?", [None, "Geral"]),
    ("Aeroporto de Axixá", None),
    ("Escola de Hogwarts", [None, "Geral: escolas"]),
    ("xyz123", None),
    ("", {"erro": "Pergunta vazia"})
]

@pytest.mark.parametrize("pergunta, esperado", CENARIOS)
def test_100_cenarios(client, pergunta, esperado):
    if pergunta == "":
        response = client.post('/chat', json={'pergunta': pergunta})
        assert response.status_code == 400
        assert response.get_json() == esperado
        return
    
    data = post_pergunta(client, pergunta)
    local_nome = str(data.get('local_nome'))
    
    if esperado is None:
        if "Hogwarts" in pergunta: 
             assert local_nome == "None" or "Geral" in local_nome
        else:
             assert local_nome == "None"
             
    elif isinstance(esperado, list):
        match = False
        for op in esperado:
            if op is None:
                if local_nome == "None": match = True
            elif op in local_nome:
                match = True
        
        assert match, f"Falha em '{pergunta}'. Recebido: '{local_nome}'. Esperado um de: {esperado}"
    else:
        assert expected_match(local_nome, esperado), f"Falha em '{pergunta}'. Recebido: '{local_nome}'. Esperado: '{esperado}'"

def expected_match(recebido, esperado):
    if recebido == "None" and esperado is None: return True
    return esperado in recebido
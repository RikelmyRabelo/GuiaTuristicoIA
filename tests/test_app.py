import sys
import os
import pytest
from unittest.mock import patch


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    

    with patch('app.conversar_com_chat') as mock_chat:
        mock_chat.return_value = "Resposta simulada da IA: O local é muito interessante. Juçara é ótima. Axixá tem muita história."
        
        with app.test_client() as client:
            yield client

def post_pergunta(client, texto):
    return client.post('/chat', json={'pergunta': texto}).get_json()

@pytest.mark.parametrize("pergunta", [
    "Olá", "Olá, tudo bem?", "Oi guia", "Opa", "Bom dia", "Boa tarde"
])
def test_saudacoes(client, pergunta):
    data = post_pergunta(client, pergunta)
    assert data['local_nome'] == "Saudação"
    assert "Sou o Guia Digital" in data['resposta']

@pytest.mark.parametrize("pergunta", [
    "Quem é você?", "Quem criou esse sistema?", 
    "Quem são os desenvolvedores?", "Fale sobre o projeto"
])
def test_identidade(client, pergunta):
    data = post_pergunta(client, pergunta)
    assert data['local_nome'] in ["Créditos", "Info dos Criadores"]
    assert "Guilherme" in data['resposta'] or "Rikelmy" in data['resposta']



@pytest.mark.parametrize("pergunta, esperado", [
    ("Onde fica a Unidade Integrada Major Fontoura?", "Unidade Integrada Major Fontoura"),
    ("Onde fica a escola Major Fontoura?", "Unidade Integrada Major Fontoura"),
    ("Onde fica o IEMA?", "IEMA - Unidade Plena de Axixá"),
    ("Escola no povoado Perijuçara", "UI Professor Manoel Santana Baldez"),                
    ("Escola no Vale Quem Tem", "UI Arcelino Rodrigues Tavares"),
    ("Onde fica a escola Axixaense?", "UE Axixaense"),
    ("Tem alguma creche?", "Jardim de Infância Adelino Fontoura"),                         
    ("Onde fica o Colégio Militar?", "Colégio Militar Tiradentes XV - Axixá"),
    ("Escola Dr. Saturnino Belo", "UE Dr. Saturnino Belo"),
    ("Escola no Bomfim", "UE Joaquim Silva")
])
def test_busca_escolas(client, pergunta, esperado):
    data = post_pergunta(client, pergunta)
    assert data['local_nome'] == esperado
@pytest.mark.parametrize("pergunta, esperado_parcial", [
    ("Onde comprar roupas?", ["Josy Boutique", "La Vista", "Top20", "Dany"]),
    ("Onde fica a Eli Lojas?", ["Eli Lojas"]),
    ("Loja de móveis", ["Eli Lojas", "Mayra Magazine", "Lunna"]),
    ("Tem farmácia na cidade?", ["Farmale"]),
    ("Material de construção", ["Comercial Martins"]),
    ("Onde tem conveniência?", ["Pit Stop"]),
    ("Distribuidora de bebidas", ["N.C. Distribuidora"]),
    ("Mercadinho no Riachão", ["Comercial Silva"])
])
def test_busca_lojas(client, pergunta, esperado_parcial):
    data = post_pergunta(client, pergunta)
    encontrado = data['local_nome']
    assert any(e in encontrado for e in esperado_parcial) or encontrado in esperado_parcial
@pytest.mark.parametrize("pergunta, esperado", [
    ("Onde tomar banho de rio?", "Ilha de Perijuçara"),
    ("Onde fica a Igreja da Luz?", "Igreja da Luz"),
    ("Onde fica a praça principal?", "Praça e Igreja do Centro"),
    ("Existem ruínas na cidade?", "Ruinas do Quilombo de Munim Mirim"),
    ("Onde fica o Balneário Santa Vitória?", "Balneario Santa Vitória")
])
def test_busca_turismo(client, pergunta, esperado):
    data = post_pergunta(client, pergunta)
    assert data['local_nome'] == esperado
@pytest.mark.parametrize("pergunta, esperado", [
    ("Endereço da prefeitura", "Prefeitura Municipal de Axixá"),
    ("Onde fica a secretaria de saúde?", "Secretaria Municipal de Saúde (SEMUS)"),
    ("Onde fica o CRAS?", "Centro de Referencia de Assistência Social - CRAS"),
    ("Onde fica a câmara municipal?", "Câmara Municipal de Axixá")
])
def test_busca_servicos(client, pergunta, esperado):
    data = post_pergunta(client, pergunta)
    assert data['local_nome'] == esperado
@pytest.mark.parametrize("pergunta, lista_esperada", [
    ("Onde fica a igreja matriz?", ["Paróquia Nossa Senhora da Saúde", "Praça e Igreja do Centro"]),
    ("Igreja Assembleia de Deus", ["Igreja Evangélica Assembleia de Deus"]),
    ("Igreja Batista", ["Igreja Batista de Jesus Cristo"])
])
def test_busca_religiao(client, pergunta, lista_esperada):
    data = post_pergunta(client, pergunta)
    assert data['local_nome'] in lista_esperada
@pytest.mark.parametrize("pergunta, esperado", [
    ("Onde fica o estádio municipal?", "Campo Municipal / Estádio"),
    ("Tem ginásio de esportes?", "Ginásio Poliesportivo José Pedro Ferreira Reis"),
    ("Campo do Riachão", "Campo do Riachão")
])
def test_busca_esportes(client, pergunta, esperado):
    data = post_pergunta(client, pergunta)
    assert data['local_nome'] == esperado
@pytest.mark.parametrize("pergunta, esperado", [
    ("Onde fica o cemitério municipal?", "Cemitério Municipal de Axixá"),
    ("Cemitério do Bomfim", "Cemitério do Bomfim")
])
def test_busca_cemiterios(client, pergunta, esperado):
    data = post_pergunta(client, pergunta)
    assert data['local_nome'] == esperado
@pytest.mark.parametrize("pergunta, esperado", [
    ("Tem onde dormir na cidade?", "Recanto Azeite Doce"),
    ("Onde tem juçara?", "Juçara"),
    ("Onde comer peixe assado?", "Peixe Assado")
])
def test_hospedagem_comida_item(client, pergunta, esperado):
    data = post_pergunta(client, pergunta)
    assert expected_match(data, esperado)

def expected_match(data, esperado):
    local = str(data.get('local_nome', ''))
    resp = str(data.get('resposta', ''))
    return esperado in local or esperado in resp

def test_lista_comidas_tipicas(client):
    data = post_pergunta(client, "Quais as comidas típicas?")
    assert data['local_nome'] in ["Lista de Comidas", "Comidas Típicas"]

def test_historia_cidade(client):
    data = post_pergunta(client, "Conte a história de Axixá")
    assert data['local_nome'] in ["História", "Dados Históricos"]

def test_fluxo_contexto(client):
    resp1 = client.post('/chat', json={'pergunta': 'Onde fica o IEMA?'}).get_json()
    assert "IEMA" in str(resp1['local_nome'])
    
    historico = [
        {"role": "user", "content": "Onde fica o IEMA?"},
        {"role": "assistant", "content": resp1['resposta']}
    ]
    
    resp2 = client.post('/chat', json={
        'pergunta': 'Fica perto do centro?',
        'historico': historico
    }).get_json()
    
    assert resp2['resposta'] is not None

def test_links_mapa(client):
    data = post_pergunta(client, "Onde fica a Prefeitura?")
    assert data['mapa_link'] is not None
    assert "google" in data['mapa_link']

def test_negativos(client):
    data = post_pergunta(client, "Onde fica a Escola de Hogwarts?")
    assert data['local_nome'] is None
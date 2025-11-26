import sys
import os
import json
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
            if "bolo" in pergunta.lower() or "hogwarts" in pergunta.lower():
                yield "Desculpe, sou apenas um guia de Axixá e não posso ajudar com esse assunto."
            elif item_data and "povoados" in str(item_data):
                yield "A cidade é cheia de povoados, você quer algum específico?"
            else:
                yield "Resposta simulada da IA."
            
        mock_chat.side_effect = side_effect
        with app.test_client() as client:
            yield client
            
    limiter.enabled = True

def post_pergunta(client, texto):
    response = client.post('/chat', json={'pergunta': texto})
    
    content = response.data.decode('utf-8')
    lines = content.split('\n')
    
    try:
        data = json.loads(lines[0])
    except:
        data = {"resposta": "", "local_nome": None, "mapa_link": None}

    # Se for uma streaming response, a resposta estará nas linhas seguintes;
    # caso contrário, mantenha o campo 'resposta' presente no JSON retornado.
    # Somente sobrescrever resposta se houver verdadeiros chunks (linhas não vazias)
    if any(l.strip() for l in lines[1:]):
        data['resposta'] = "".join(lines[1:])
    return data

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

@pytest.mark.parametrize("pergunta, esperado", [
    ("Onde fica a Unidade Integrada Major Fontoura?", "Unidade Integrada Major Fontoura"),
    ("Onde fica o IEMA?", "IEMA - Unidade Plena de Axixá"),
    ("Escola no povoado Perijuçara", "UI Professor Manoel Santana Baldez"),                
    ("Tem alguma creche?", "Jardim de Infância Adelino Fontoura"),                         
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
    ("Mercadinho no Riachão", ["Comercial Silva"])
])
def test_busca_lojas(client, pergunta, esperado_parcial):
    data = post_pergunta(client, pergunta)
    encontrado = str(data['local_nome'])
    assert any(e in encontrado for e in esperado_parcial) or "Geral" in encontrado

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

@pytest.mark.parametrize("pergunta, esperado", [
    ("Onde fica o estádio municipal?", "Campo Municipal / Estádio"),
    ("Tem ginásio de esportes?", ["Ginásio", "Geral"]),
    ("Campo do Riachão", "Campo do Riachão")
])
def test_busca_esportes(client, pergunta, esperado):
    data = post_pergunta(client, pergunta)
    local = str(data['local_nome'])
    if isinstance(esperado, list):
        assert any(e in local for e in esperado)
    else:
        assert esperado in local

@pytest.mark.parametrize("pergunta, esperado", [
    ("Tem onde dormir na cidade?", ["Recanto Azeite Doce", "Geral"]),
    ("Onde tem juçara?", "Juçara"),
    ("Onde comer peixe assado?", "Peixe Assado")
])
def test_hospedagem_comida_item(client, pergunta, esperado):
    data = post_pergunta(client, pergunta)
    local = str(data.get('local_nome', ''))
    
    if isinstance(esperado, list):
        assert any(e in local for e in esperado)
    else:
        assert expected_match(data, esperado)

def expected_match(data, esperado):
    local = str(data.get('local_nome', ''))
    resp = str(data.get('resposta', ''))
    return esperado in local or esperado in resp

def test_negativos(client):
    data = post_pergunta(client, "Onde fica a Escola de Hogwarts?")
    assert data['local_nome'] is None or "Geral" in data['local_nome']

@pytest.mark.parametrize("pergunta", [
    "Escola em Axixá", 
    "Quero ver lojas", 
    "Tem igrejas?"
])
def test_busca_geral_categorias(client, pergunta):
    data = post_pergunta(client, pergunta)
    assert "Geral:" in str(data['local_nome'])
    assert "povoados" in data['resposta'].lower()
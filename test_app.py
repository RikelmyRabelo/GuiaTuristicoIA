import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def post_pergunta(client, texto):
    return client.post('/chat', json={'pergunta': texto}).get_json()


def test_saudacao_basica(client):
    data = post_pergunta(client, "Olá, tudo bem?")
    assert "Sou o Guia Digital" in data['resposta']
    assert data['local_nome'] == "Saudação"

def test_quem_desenvolveu(client):
    data = post_pergunta(client, "Quem criou esse sistema?")
    assert "Rikelmy" in data['resposta']
    assert data['local_nome'] == "Info dos Criadores"

def test_igreja_da_luz(client):
    data = post_pergunta(client, "Onde fica a igreja da luz?")
    assert data['local_nome'] == "Igreja da Luz"

def test_escola_major_fontoura(client):
    data = post_pergunta(client, "Onde fica a escola Major Fontoura?")
    assert data['local_nome'] == "Unidade Integrada Major Fontoura"

def test_comidas_tipicas(client):
    data = post_pergunta(client, "Quais são as comidas típicas?")
    assert "Juçara" in data['resposta'] or "Peixe" in data['resposta']


def test_escola_santa_rosa(client):
    data = post_pergunta(client, "Escola em Santa Rosa")
    locais_validos = [
        "Jardim de Infância Lilian Cortes Maciel Vieira", 
        "IEMA - Unidade Plena de Axixá",
        "UI Delarey Cardoso Nunes"
    ]
    assert data['local_nome'] in locais_validos

def test_moveis(client):
    data = post_pergunta(client, "Onde compro móveis?")
    locais_validos = ["Eli Lojas", "Mayra Magazine", "Lunna Eletromóveis"]
    assert data['local_nome'] in locais_validos


def test_pergunta_negativa(client):
    data = post_pergunta(client, "Existe uma igreja de São Benedito?")
    assert data['local_nome'] is None

@pytest.mark.parametrize("pergunta, esperado_parcial", [
    ("Onde fica a Prefeitura?", "Prefeitura Municipal"),
    ("Onde fica o CRAS?", "CRAS"),
    ("Tem alguma pousada?", "Recanto Azeite Doce"),
    ("Onde tem estádio de futebol?", "Campo Municipal"),
])
def test_varios_locais(client, pergunta, esperado_parcial):
    data = post_pergunta(client, pergunta)
    assert data['local_nome'] is not None
    assert esperado_parcial in data['local_nome']
import os
from dotenv import load_dotenv

load_dotenv()

# Configurações de API
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-chat"

# Configurações de Banco de Dados
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Constantes do Projeto
CATEGORIAS_ALVO = [
    "pontos_turisticos", "escolas", "lojas", "predios_municipais", 
    "igrejas", "campos_esportivos", "cemiterios", "pousadas_dormitorios", 
    "comidas_tipicas"
]

CATEGORY_KEYWORDS_MAP = {
    "escolas": ["escola", "colegio", "creche", "estudar", "ensino", "infancia", "fundamental", "medio", "educacao", "unidade"],
    "lojas": ["loja", "comprar", "mercado", "vende", "roupa", "moda", "moveis", "eletro", "calcados", "flor", "variedade", "material", "construcao", "floricultura", "mercadinho", "farmacia", "conveniencia", "distribuidora"],
    "pontos_turisticos": ["turismo", "passear", "banho", "rio", "praca", "igreja", "visitar", "ruina", "lazer", "turistico", "historico", "balneario"],
    "igrejas": ["igreja", "paroquia", "culto", "missa", "evangelica", "catolica", "assembleia", "batista"],
    "predios_municipais": ["prefeitura", "secretaria", "cras", "camara", "orgao", "publico", "saude", "assistencia"],
    "campos_esportivos": ["campo", "futebol", "ginasio", "jogo", "esporte", "quadra", "bola"],
    "cemiterios": ["cemiterio", "sepultamento", "enterrar"],
    "pousadas_dormitorios": ["pousada", "dormir", "hotel", "hospedagem", "quarto", "dormitorio"],
    "comidas_tipicas": ["comida", "tipica", "prato", "fome", "comer", "restaurante", "gastronomia", "culinaria", "almoco", "jantar", "peixe", "jucara"]
}

STOP_WORDS = {
    'a', 'o', 'e', 'ou', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 
    'nos', 'nas', 'por', 'para', 'com', 'sem', 'sob', 'sobre', 
    'me', 'fale', 'diga', 'onde', 'fica', 'localiza', 'localizacao', 'qual', 'quais', 'sao', 'sou',
    'gostaria', 'queria', 'saber', 'informacoes', 'info', 'axixa', 'cidade', 'municipio',
    'ola', 'oi', 'como', 'faco', 'pra', 'chegar', 'quero',
    'tem', 'tinha', 'existe', 'ha', 'que', 'alguma', 'algum', 'uns', 'umas',
    'bairro', 'rua', 'av', 'avenida', 'povoado'
}
CATEGORIAS_ALVO = [
    "pontos_turisticos", "escolas", "lojas", "predios_municipais", 
    "igrejas", "campos_esportivos", "cemiterios", "pousadas_dormitorios", 
    "comidas_tipicas"
]

CATEGORY_KEYWORDS_MAP = {
    "escolas": ["escola", "colegio", "creche", "estudar", "ensino", "infancia", "fundamental", "medio", "educacao", "unidade"],
    "lojas": ["loja", "comprar", "mercado", "vende", "roupa", "moda", "moveis", "eletro", "calcados", "flor", "variedade", "material", "construcao", "floricultura", "mercadinho", "farmacia", "conveniencia", "distribuidora"],
    "pontos_turisticos": ["turismo", "passear", "banho", "rio", "praca", "igreja", "visitar", "ruina", "lazer", "turistico", "historico", "balneario", "praia"],
    "igrejas": ["igreja", "paroquia", "culto", "missa", "evangelica", "catolica", "assembleia", "batista"],
    "predios_municipais": ["prefeitura", "secretaria", "cras", "camara", "orgao", "publico", "saude", "assistencia"],
    "campos_esportivos": ["campo", "futebol", "ginasio", "jogo", "esporte", "quadra", "bola"],
    "cemiterios": ["cemiterio", "sepultamento", "enterrar"],
    "pousadas_dormitorios": ["pousada", "dormir", "hotel", "hospedagem", "quarto", "dormitorio"],
    "comidas_tipicas": ["comida", "tipica", "prato", "fome", "comer", "restaurante", "gastronomia", "culinaria", "almoco", "jantar", "peixe", "jucara"]
}

STOP_WORDS = {
    'a', 'o', 'e', 'ou', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 
    'nos', 'nas', 'por', 'para', 'com', 'sem', 'sob', 'sobre', 'as', 'os',
    'me', 'fale', 'diga', 'onde', 'fica', 'localiza', 'localizacao', 'qual', 
    'quais', 'sao', 'sou', 'gostaria', 'queria', 'saber', 'informacoes', 'info', 
    'axixa', 'cidade', 'municipio', 'como', 'faco', 'pra', 'chegar', 
    'quero', 'tem', 'tinha', 'existe', 'existem', 'ha', 'que', 'alguma', 'algum', 
    'uns', 'umas', 'bairro', 'rua', 'av', 'avenida', 'povoado',
    'tomar', 'fazer', 'encontrar', 'posso', 'pode', 'endereco', 
    'ver', 'comprar', 'vende'
}

SAUDACOES_WORDS = {"ola", "oi", "opa", "salve", "eai"}
SAUDACOES_PHRASES = ["bom dia", "boa tarde", "boa noite", "tudo bem", "tude bem", "como vai"]

IDENTITY_KEYWORDS = [
    "quem fez", "quem criou", "quem desenvolveu", "criador", "desenvolvedor", 
    "quem e voce", "quem saoz", "sobre o projeto", "quem sou eu"
]
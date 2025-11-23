from rapidfuzz import process, fuzz
from src.utils import normalize_text
from src.constants import CATEGORIAS_ALVO, CATEGORY_KEYWORDS_MAP, STOP_WORDS

SEARCH_CACHE = {}

# Termos que, se forem a única coisa na busca, forçam o retorno da lista geral
GENERIC_TRIGGERS = {
    "escolas": ["escola", "escolas", "colegio", "colegios", "estudar"],
    "lojas": ["loja", "lojas", "comercio", "compras"],
    "igrejas": ["igreja", "igrejas"],
    "pontos_turisticos": ["turismo", "passear", "pontos turisticos"],
    "predios_municipais": ["orgaos", "predios", "reparticoes"],
    "campos_esportivos": ["esportes", "campos", "ginasio"],
    "cemiterios": ["cemiterio", "cemiterios"],
    "pousadas_dormitorios": ["dormir", "pousada", "pousadas"],
    "comidas_tipicas": ["comida", "comer"]
}

def build_search_index(data: dict):
    global SEARCH_CACHE
    if not data: return
    
    for categoria in CATEGORIAS_ALVO:
        items = data.get(categoria, [])
        processed_texts = []
        processed_objects = []

        for item in items:
            nome = item.get("nome") or item.get("orgao") or ""
            local = item.get("localizacao") or item.get("endereco") or ""
            desc = item.get("descricao") or item.get("descrição") or ""
            
            # CORREÇÃO: Não injetamos mais as palavras-chave da categoria no texto do item.
            # Isso evita que uma loja de roupas seja encontrada quando se busca "farmácia".
            texto_cru = f"{nome} {desc} {local} {categoria}"
            texto_busca = normalize_text(texto_cru)
            
            item["_nome_normalizado"] = normalize_text(nome)
            
            processed_texts.append(texto_busca)
            processed_objects.append(item)
        
        SEARCH_CACHE[categoria] = {
            "texts": processed_texts,
            "objects": processed_objects
        }

def find_item_smart(pergunta: str):
    if not pergunta: return None

    pergunta_limpa = normalize_text(pergunta)
    # Filtra stop words e palavras muito curtas
    termos_importantes = [word for word in pergunta_limpa.split() if word not in STOP_WORDS and len(word) > 1]
    
    if termos_importantes:
        query_final = " ".join(termos_importantes)
    else:
        query_final = pergunta_limpa

    # 1. Verificação de Busca Genérica Exata
    # Se o usuário digitou apenas "escola" ou "lojas", retornamos a lista geral.
    for categoria, triggers in GENERIC_TRIGGERS.items():
        if query_final in triggers:
            all_items = SEARCH_CACHE.get(categoria, {}).get("objects", [])
            return {
                "is_general": True,
                "category": categoria,
                "items": all_items[:4]
            }

    best_item = None
    best_score = 0
    detected_category = None

    # 2. Busca Difusa (Fuzzy Search)
    for categoria in CATEGORIAS_ALVO:
        cat_bonus = 0
        keywords = CATEGORY_KEYWORDS_MAP.get(categoria, [])
        
        # Bônus se a categoria foi mencionada na pergunta
        if any(kw in query_final for kw in keywords):
            cat_bonus = 10
            if not detected_category:
                detected_category = categoria

        cache_data = SEARCH_CACHE.get(categoria)
        if not cache_data or not cache_data["texts"]: continue
            
        match = process.extractOne(query_final, cache_data["texts"], scorer=fuzz.token_set_ratio)
        
        if match:
            _, score_base, index = match
            item_match = cache_data["objects"][index]
            nome_norm = item_match.get("_nome_normalizado", "")
            
            current_score = score_base
            
            # Bônus apenas para match forte de NOME (não descrição)
            name_score = fuzz.token_set_ratio(query_final, nome_norm)
            
            if name_score > 90:
                current_score += 15
            elif name_score > 70:
                current_score += 5
            
            score_final = current_score + cat_bonus

            if score_final > best_score:
                best_score = score_final
                best_item = item_match

    # Limite 75: Evita falsos positivos (ex: "Escola Hogwarts" não deve achar uma escola real aleatória)
    if best_score >= 75:
        return best_item
    
    # Se não atingiu score para um item específico, mas detectou a intenção da categoria, retorna Geral
    if detected_category:
        all_items = SEARCH_CACHE[detected_category]["objects"]
        return {
            "is_general": True,
            "category": detected_category,
            "items": all_items[:4] 
        }

    return None
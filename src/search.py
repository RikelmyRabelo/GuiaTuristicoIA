from rapidfuzz import process, fuzz
from src.utils import normalize_text
from src.constants import CATEGORIAS_ALVO, CATEGORY_KEYWORDS_MAP, STOP_WORDS

SEARCH_CACHE = {}

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
    termos_importantes = [word for word in pergunta_limpa.split() if word not in STOP_WORDS and len(word) > 1]
    
    # Se sobrou algo, usa. Senão usa a original.
    if termos_importantes:
        query_final = " ".join(termos_importantes)
    else:
        query_final = pergunta_limpa

    best_item = None
    best_score = 0

    for categoria in CATEGORIAS_ALVO:
        cat_bonus = 0
        keywords = CATEGORY_KEYWORDS_MAP.get(categoria, [])
        
        # Bônus de Categoria
        if any(kw in query_final for kw in keywords):
            cat_bonus = 10

        cache_data = SEARCH_CACHE.get(categoria)
        if not cache_data or not cache_data["texts"]: continue
            
        # Busca principal
        match = process.extractOne(query_final, cache_data["texts"], scorer=fuzz.token_set_ratio)
        
        if match:
            _, score_base, index = match
            item_match = cache_data["objects"][index]
            nome_norm = item_match.get("_nome_normalizado", "")
            
            # Bônus de Nome Exato
            name_score = fuzz.token_set_ratio(query_final, nome_norm)
            if name_score > 85:
                score_base += 25
            elif name_score > 60:
                score_base += 10
            
            score_final = score_base + cat_bonus

            if score_final > best_score:
                best_score = score_final
                best_item = item_match

    if best_score >= 70:
        return best_item

    return None
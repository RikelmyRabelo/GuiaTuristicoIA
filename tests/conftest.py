import json
import pytest
import requests
import app as appmod
import src.llm as llm


def _fake_streaming_generator(response_chunks=None):
    if response_chunks is None:
        response_chunks = ["Resposta simulada da IA."]
    for chunk in response_chunks:
        yield chunk


def _fake_conversar_com_chat(pergunta, system_prompt, item_data_json=None, historico=None):
    texto = str(pergunta).lower() if pergunta else ""
    # Comportamento similar aos testes existentes
    if "bolo" in texto or "hogwarts" in texto:
        yield "Desculpe, sou apenas um guia de Axixá e não posso ajudar com esse assunto."
    elif item_data_json and ("povoados" in str(item_data_json).lower() or "povoado" in str(item_data_json).lower()):
        yield "A cidade é cheia de povoados, você quer algum específico?"
    else:
        # Detecção por palavra-chave para tornar o mock mais útil para cenários
        if "escola" in texto or (item_data_json and "escolas" in str(item_data_json).lower()):
            yield from _fake_streaming_generator(["A cidade tem vários povoados. ", "Posso listar as escolas por povoado se quiser."])
            return
        if "loja" in texto or (item_data_json and "lojas" in str(item_data_json).lower()):
            yield from _fake_streaming_generator(["Tem várias lojas locais, como Josy Boutique, Eli Lojas e Dany Multimarcas. ", "Quer uma lista completa?"])
            return
        if "igreja" in texto or (item_data_json and "igrejas" in str(item_data_json).lower()):
            yield from _fake_streaming_generator(["A cidade tem igrejas em diversos povoados e no centro. ", "Posso indicar endereços."])
            return
        # Simula múltiplos chunks (como streamed responses)
        yield from _fake_streaming_generator(["Primeiro pedaço da resposta.", " Segunda parte da resposta."])


@pytest.fixture(autouse=True)
def block_external_and_mock_llm(monkeypatch):
    # Mocka a função do módulo llm para evitar chamadas reais
    monkeypatch.setattr(llm, "conversar_com_chat", _fake_conversar_com_chat)

    # Impede qualquer chamada real ao requests.post (evita consumo de créditos acidental)
    def _blocked_requests_post(*args, **kwargs):
        raise RuntimeError("Chamadas HTTP externas estão bloqueadas durante os testes. Use mocks.")

    monkeypatch.setattr(requests, "post", _blocked_requests_post)

    # Permite que o resto dos testes sejam executados
    yield

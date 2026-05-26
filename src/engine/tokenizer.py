"""Tokenizador minimalista e determinístico.

Regras:
    * texto convertido para lowercase via str.lower()
    * acentos / diacríticos removidos via normalização Unicode NFD
      (compatibilidade entre "árvore" e "arvore" em buscas/autocomplete)
    * caracteres não-alfanuméricos atuam como separadores
    * palavras com menos de 2 caracteres são descartadas (stop)
    * stopwords mínimas em PT/EN para evitar inflar o índice

A função é puramente determinística — mesma entrada => mesma saída.
"""

from __future__ import annotations

import unicodedata
from typing import Iterable, List


def _strip_accents(text: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )

# Stopwords curtas, suficientes para o cenário de exemplo. NÃO incluímos
# uma lista enorme para não mascarar o comportamento do índice invertido.
_STOPWORDS = frozenset(
    {
        "a", "o", "e", "de", "da", "do", "das", "dos", "um", "uma",
        "para", "por", "com", "em", "no", "na", "nos", "nas", "que",
        "se", "ao", "à", "às", "os", "as", "the", "and", "of", "to",
        "in", "is", "it", "for", "on", "with", "as", "at", "by",
    }
)


def tokenize(text: str) -> List[str]:
    if not text:
        return []
    normalized = _strip_accents(text).lower()
    tokens: List[str] = []
    current_chars: List[str] = []
    for ch in normalized:
        if ch.isalnum():
            current_chars.append(ch)
        else:
            if current_chars:
                token = "".join(current_chars)
                if len(token) >= 2 and token not in _STOPWORDS:
                    tokens.append(token)
                current_chars.clear()
    if current_chars:
        token = "".join(current_chars)
        if len(token) >= 2 and token not in _STOPWORDS:
            tokens.append(token)
    return tokens


def tokenize_many(texts: Iterable[str]) -> List[str]:
    """Concatena os tokens de vários textos preservando a ordem."""
    out: List[str] = []
    for text in texts:
        out.extend(tokenize(text))
    return out

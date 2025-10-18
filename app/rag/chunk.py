"""
Utilitário simples de chunking de texto para RAG.

- Quebra texto em janelas com sobreposição configurável.
- Não usa variáveis de ambiente.
"""

from typing import List


def simple_chunk(text: str, max_chars: int = 1000, overlap: int = 100) -> List[str]:
    """Divide `text` em chunks com tamanho máximo e sobreposição.

    Parâmetros:
    - max_chars: tamanho máximo de cada chunk (caracteres).
    - overlap: quantidade de sobreposição entre chunks (caracteres).
    """
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = end - overlap
        if start < 0:
            start = 0
    return chunks
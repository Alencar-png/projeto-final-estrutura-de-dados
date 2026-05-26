"""HeapSort e seleção de Top-K implementados manualmente.

RF04 — Utilizado pelo motor RAG para devolver o Top-5 documentos por relevância.

Funções expostas:
    heap_sort(items, key=None, reverse=False)  -> List ordenada (in-place style)
    top_k(items, k, key=None, reverse=True)    -> List com os K maiores/menores

Complexidade:
    heap_sort -> O(N log N) tempo, O(1) memória adicional
    top_k     -> O(N log K) tempo, O(K) memória adicional
                 (usando uma min-heap de tamanho K para extrair os maiores)
"""

from __future__ import annotations

from typing import Callable, List, Optional, TypeVar

T = TypeVar("T")


def _default_key(x):
    return x


def _sift_down_max(arr: List[T], start: int, end: int, key: Callable[[T], object]) -> None:
    """Sift-down para construção de max-heap."""
    root = start
    while True:
        child = 2 * root + 1
        if child > end:
            return
        # escolhe o maior dos filhos
        if child + 1 <= end and key(arr[child]) < key(arr[child + 1]):
            child += 1
        if key(arr[root]) < key(arr[child]):
            arr[root], arr[child] = arr[child], arr[root]
            root = child
        else:
            return


def _sift_down_min(arr: List[T], start: int, end: int, key: Callable[[T], object]) -> None:
    root = start
    while True:
        child = 2 * root + 1
        if child > end:
            return
        if child + 1 <= end and key(arr[child]) > key(arr[child + 1]):
            child += 1
        if key(arr[root]) > key(arr[child]):
            arr[root], arr[child] = arr[child], arr[root]
            root = child
        else:
            return


def heap_sort(
    items: List[T],
    key: Optional[Callable[[T], object]] = None,
    reverse: bool = False,
) -> List[T]:
    """Ordena `items` em ordem crescente (ou decrescente se reverse=True).

    Implementação clássica em duas fases:
      1. Heapify: O(N) construindo a heap a partir do meio do array.
      2. Extração: N-1 trocas com a raiz + sift-down -> O(N log N).

    A função devolve a mesma lista ordenada (também modifica in-place).
    """
    if key is None:
        key = _default_key
    n = len(items)
    if n <= 1:
        return items

    if not reverse:
        # max-heap -> ordem crescente
        for start in range(n // 2 - 1, -1, -1):
            _sift_down_max(items, start, n - 1, key)
        for end in range(n - 1, 0, -1):
            items[0], items[end] = items[end], items[0]
            _sift_down_max(items, 0, end - 1, key)
    else:
        # min-heap -> ordem decrescente
        for start in range(n // 2 - 1, -1, -1):
            _sift_down_min(items, start, n - 1, key)
        for end in range(n - 1, 0, -1):
            items[0], items[end] = items[end], items[0]
            _sift_down_min(items, 0, end - 1, key)
    return items


# ----------------------------------------------------------------- Top-K
def _sift_up_min(heap: List[T], idx: int, key: Callable[[T], object]) -> None:
    while idx > 0:
        parent = (idx - 1) // 2
        if key(heap[idx]) < key(heap[parent]):
            heap[idx], heap[parent] = heap[parent], heap[idx]
            idx = parent
        else:
            return


def _sift_down_min_full(heap: List[T], idx: int, key: Callable[[T], object]) -> None:
    n = len(heap)
    while True:
        left = 2 * idx + 1
        right = 2 * idx + 2
        smallest = idx
        if left < n and key(heap[left]) < key(heap[smallest]):
            smallest = left
        if right < n and key(heap[right]) < key(heap[smallest]):
            smallest = right
        if smallest == idx:
            return
        heap[idx], heap[smallest] = heap[smallest], heap[idx]
        idx = smallest


def top_k(
    items,
    k: int,
    key: Optional[Callable[[T], object]] = None,
    reverse: bool = True,
) -> List[T]:
    """Seleciona o Top-K elementos de `items`.

    Args:
        items: iterável.
        k: quantidade máxima de itens.
        key: função de extração da chave de comparação.
        reverse: True (default) -> Top-K MAIORES. False -> Top-K MENORES.

    Estratégia:
        Mantém uma heap de tamanho K. Para Top-K maiores usamos uma
        min-heap (o menor dos K maiores fica na raiz e é descartado
        quando aparece um valor maior). Top-K menores é simétrico
        (max-heap de tamanho K).

    Complexidade: O(N log K) tempo, O(K) memória.
    """
    if key is None:
        key = _default_key
    if k <= 0:
        return []

    if reverse:
        # min-heap dos K maiores (raiz = menor dos K maiores correntes)
        heap: List[T] = []
        for item in items:
            if len(heap) < k:
                heap.append(item)
                _sift_up_min(heap, len(heap) - 1, key)
            elif key(item) > key(heap[0]):
                heap[0] = item
                _sift_down_min_full(heap, 0, key)
        heap_sort(heap, key=key, reverse=True)
        return heap
    else:
        # max-heap dos K menores (raiz = maior dos K menores correntes)
        heap: List[T] = []
        for item in items:
            if len(heap) < k:
                heap.append(item)
                _sift_up_max(heap, len(heap) - 1, key)
            elif key(item) < key(heap[0]):
                heap[0] = item
                _sift_down_max_full(heap, 0, key)
        heap_sort(heap, key=key, reverse=False)
        return heap


def _sift_up_max(heap: List[T], idx: int, key: Callable[[T], object]) -> None:
    while idx > 0:
        parent = (idx - 1) // 2
        if key(heap[idx]) > key(heap[parent]):
            heap[idx], heap[parent] = heap[parent], heap[idx]
            idx = parent
        else:
            return


def _sift_down_max_full(heap: List[T], idx: int, key: Callable[[T], object]) -> None:
    n = len(heap)
    while True:
        left = 2 * idx + 1
        right = 2 * idx + 2
        largest = idx
        if left < n and key(heap[left]) > key(heap[largest]):
            largest = left
        if right < n and key(heap[right]) > key(heap[largest]):
            largest = right
        if largest == idx:
            return
        heap[idx], heap[largest] = heap[largest], heap[idx]
        idx = largest

"""Tabela Hash com tratamento de colisões por encadeamento separado.

RF01 — Estrutura primária utilizada pelo Índice Invertido do Motor RAG.

Complexidade média (com função de hash bem distribuída):
    put(k, v)     -> O(1)
    get(k)        -> O(1)
    remove(k)     -> O(1)
    contains(k)   -> O(1)
    rehash()      -> O(N) amortizado

Pior caso (todas as chaves colidem): O(N) por operação.
Mantemos o fator de carga <= LOAD_FACTOR_MAX para evitar degradação.
"""

from __future__ import annotations

from typing import Any, Callable, Iterator, List, Optional, Tuple


class _Node:
    """Nó da lista encadeada usada em cada bucket."""

    __slots__ = ("key", "value", "next")

    def __init__(self, key: Any, value: Any, nxt: Optional["_Node"] = None) -> None:
        self.key = key
        self.value = value
        self.next: Optional[_Node] = nxt


class HashTable:
    """Tabela Hash genérica com encadeamento separado.

    A função de hash padrão é uma variação do DJB2 (Daniel J. Bernstein),
    escolhida pela boa distribuição em chaves textuais (cenário do RAG).
    """

    LOAD_FACTOR_MAX = 0.75
    INITIAL_CAPACITY = 16
    _PRIMES_MULT = 1099511628211  # FNV prime (apenas usado como multiplicador auxiliar)

    def __init__(
        self,
        capacity: int = INITIAL_CAPACITY,
        hash_fn: Optional[Callable[[Any], int]] = None,
    ) -> None:
        if capacity <= 0:
            raise ValueError("capacity precisa ser > 0")
        self._capacity = self._next_power_of_two(capacity)
        self._buckets: List[Optional[_Node]] = [None] * self._capacity
        self._size = 0
        self._hash_fn = hash_fn or self._default_hash

    # ------------------------------------------------------------------ utils
    @staticmethod
    def _next_power_of_two(n: int) -> int:
        p = 1
        while p < n:
            p <<= 1
        return p

    @staticmethod
    def _default_hash(key: Any) -> int:
        """DJB2 estendido para inteiros, strings e tuplas.

        Importante: não usamos hash() embutido para garantir que o
        comportamento seja determinístico entre execuções
        (PYTHONHASHSEED não interfere).
        """
        if isinstance(key, int):
            x = key & 0xFFFFFFFFFFFFFFFF
            x = (x ^ (x >> 33)) * 0xFF51AFD7ED558CCD & 0xFFFFFFFFFFFFFFFF
            x = (x ^ (x >> 33)) * 0xC4CEB9FE1A85EC53 & 0xFFFFFFFFFFFFFFFF
            return x ^ (x >> 33)

        if isinstance(key, str):
            h = 5381
            for ch in key:
                h = ((h << 5) + h + ord(ch)) & 0xFFFFFFFFFFFFFFFF
            return h

        if isinstance(key, tuple):
            h = 1469598103934665603
            for item in key:
                h ^= HashTable._default_hash(item)
                h = (h * HashTable._PRIMES_MULT) & 0xFFFFFFFFFFFFFFFF
            return h

        # Fallback: usa repr() para tipos arbitrários.
        return HashTable._default_hash(repr(key))

    def _bucket_index(self, key: Any) -> int:
        return self._hash_fn(key) & (self._capacity - 1)

    # --------------------------------------------------------------- public API
    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: Any) -> bool:
        return self.get(key, _MISSING) is not _MISSING

    def __iter__(self) -> Iterator[Any]:
        return self.keys()

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def load_factor(self) -> float:
        return self._size / self._capacity

    def put(self, key: Any, value: Any) -> None:
        idx = self._bucket_index(key)
        node = self._buckets[idx]
        while node is not None:
            if node.key == key:
                node.value = value
                return
            node = node.next
        self._buckets[idx] = _Node(key, value, self._buckets[idx])
        self._size += 1
        if self.load_factor > self.LOAD_FACTOR_MAX:
            self._rehash(self._capacity * 2)

    def get(self, key: Any, default: Any = None) -> Any:
        idx = self._bucket_index(key)
        node = self._buckets[idx]
        while node is not None:
            if node.key == key:
                return node.value
            node = node.next
        return default

    def get_or_create(self, key: Any, factory: Callable[[], Any]) -> Any:
        """Retorna o valor; se não existir, cria via factory() e devolve.

        Útil para construção de índice invertido (postings list por termo).
        """
        idx = self._bucket_index(key)
        node = self._buckets[idx]
        while node is not None:
            if node.key == key:
                return node.value
            node = node.next
        value = factory()
        self._buckets[idx] = _Node(key, value, self._buckets[idx])
        self._size += 1
        if self.load_factor > self.LOAD_FACTOR_MAX:
            self._rehash(self._capacity * 2)
        return value

    def remove(self, key: Any) -> bool:
        idx = self._bucket_index(key)
        prev: Optional[_Node] = None
        node = self._buckets[idx]
        while node is not None:
            if node.key == key:
                if prev is None:
                    self._buckets[idx] = node.next
                else:
                    prev.next = node.next
                self._size -= 1
                return True
            prev = node
            node = node.next
        return False

    def keys(self) -> Iterator[Any]:
        for head in self._buckets:
            node = head
            while node is not None:
                yield node.key
                node = node.next

    def values(self) -> Iterator[Any]:
        for head in self._buckets:
            node = head
            while node is not None:
                yield node.value
                node = node.next

    def items(self) -> Iterator[Tuple[Any, Any]]:
        for head in self._buckets:
            node = head
            while node is not None:
                yield node.key, node.value
                node = node.next

    # -------------------------------------------------------------- internals
    def _rehash(self, new_capacity: int) -> None:
        old_buckets = self._buckets
        self._capacity = new_capacity
        self._buckets = [None] * new_capacity
        self._size = 0
        for head in old_buckets:
            node = head
            while node is not None:
                self.put(node.key, node.value)
                node = node.next

    def stats(self) -> dict:
        """Estatísticas usadas para prova de carga."""
        bucket_sizes = []
        for head in self._buckets:
            count = 0
            node = head
            while node is not None:
                count += 1
                node = node.next
            bucket_sizes.append(count)
        non_empty = [c for c in bucket_sizes if c > 0]
        return {
            "size": self._size,
            "capacity": self._capacity,
            "load_factor": round(self.load_factor, 4),
            "non_empty_buckets": len(non_empty),
            "max_chain": max(bucket_sizes) if bucket_sizes else 0,
            "avg_chain_non_empty": (
                round(sum(non_empty) / len(non_empty), 3) if non_empty else 0
            ),
        }


# Sentinela usada para diferenciar "ausente" de "valor None".
_MISSING = object()

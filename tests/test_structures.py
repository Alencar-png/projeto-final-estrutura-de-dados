"""Testes unitários básicos das estruturas implementadas.

Execução:
    PYTHONPATH=. python3 -m unittest tests.test_structures -v
ou
    PYTHONPATH=. python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import random
import unittest

from src.structures import HashTable, InvertedIndex, Trie, SplayTree, heap_sort, top_k


class TestHashTable(unittest.TestCase):
    def test_put_get_remove(self):
        ht = HashTable()
        ht.put("a", 1)
        ht.put("b", 2)
        self.assertEqual(ht.get("a"), 1)
        self.assertEqual(ht.get("b"), 2)
        self.assertIsNone(ht.get("c"))
        self.assertTrue(ht.remove("a"))
        self.assertFalse(ht.remove("a"))
        self.assertEqual(len(ht), 1)

    def test_overwrite(self):
        ht = HashTable()
        ht.put("x", 1)
        ht.put("x", 99)
        self.assertEqual(ht.get("x"), 99)
        self.assertEqual(len(ht), 1)

    def test_rehash_growth(self):
        ht = HashTable(capacity=4)
        for i in range(100):
            ht.put(f"k{i}", i)
        self.assertEqual(len(ht), 100)
        self.assertGreater(ht.capacity, 4)
        self.assertLessEqual(ht.load_factor, 0.75)
        for i in range(100):
            self.assertEqual(ht.get(f"k{i}"), i)

    def test_iteration(self):
        ht = HashTable()
        expected = {f"k{i}": i for i in range(50)}
        for k, v in expected.items():
            ht.put(k, v)
        self.assertEqual(dict(ht.items()), expected)

    def test_random_stress(self):
        rnd = random.Random(7)
        ht = HashTable()
        ref = {}
        for _ in range(2000):
            k = f"key_{rnd.randint(0, 500)}"
            if rnd.random() < 0.2 and ref:
                ht.remove(k)
                ref.pop(k, None)
            else:
                v = rnd.randint(0, 10_000)
                ht.put(k, v)
                ref[k] = v
        for k, v in ref.items():
            self.assertEqual(ht.get(k), v)
        self.assertEqual(len(ht), len(ref))


class TestTrie(unittest.TestCase):
    def test_insert_contains(self):
        t = Trie()
        for w in ["foo", "foobar", "bar", "baz"]:
            t.insert(w)
        self.assertTrue(t.contains("foo"))
        self.assertTrue(t.contains("foobar"))
        self.assertFalse(t.contains("foob"))
        self.assertTrue(t.starts_with("foo"))
        self.assertTrue(t.starts_with("ba"))
        self.assertFalse(t.starts_with("xyz"))

    def test_autocomplete_deterministico(self):
        t = Trie()
        for w in ["car", "cart", "cargo", "card", "cap"]:
            t.insert(w)
        self.assertEqual(t.autocomplete("ca", 10), ["cap", "car", "card", "cargo", "cart"])
        self.assertEqual(t.autocomplete("ca", 3), ["cap", "car", "card"])
        self.assertEqual(t.autocomplete("xy", 5), [])

    def test_frequency(self):
        t = Trie()
        t.insert("rag", 5)
        t.insert("rag", 2)
        self.assertEqual(t.frequency_of("rag"), 7)


class TestSplayTree(unittest.TestCase):
    def test_insert_and_root(self):
        sp = SplayTree()
        sp.insert(5, "a"); sp.insert(3, "b"); sp.insert(8, "c")
        self.assertEqual(len(sp), 3)
        self.assertEqual(sp.root_key(), 8)

    def test_get_moves_to_root(self):
        sp = SplayTree()
        for k in [50, 25, 75, 10, 30, 60, 80]:
            sp.insert(k, k * 2)
        self.assertEqual(sp.get(10), 20)
        self.assertEqual(sp.root_key(), 10)

    def test_remove(self):
        sp = SplayTree()
        for k in range(20):
            sp.insert(k, k)
        self.assertTrue(sp.remove(5))
        self.assertFalse(sp.contains(5))
        self.assertEqual(len(sp), 19)

    def test_capacity_evicts(self):
        sp = SplayTree(capacity=3)
        for k in "abcdefgh":
            sp.insert(k, k.upper())
        self.assertEqual(len(sp), 3)
        self.assertGreater(sp.evictions, 0)

    def test_in_order_after_operations(self):
        sp = SplayTree()
        keys = [4, 2, 6, 1, 3, 5, 7]
        for k in keys:
            sp.insert(k, k)
        ordered = [k for k, _ in sp.in_order()]
        self.assertEqual(ordered, sorted(keys))


class TestHeapSort(unittest.TestCase):
    def test_sort_basic(self):
        arr = [5, 2, 9, 1, 3, 7, 4]
        self.assertEqual(heap_sort(list(arr)), sorted(arr))
        self.assertEqual(heap_sort(list(arr), reverse=True), sorted(arr, reverse=True))

    def test_sort_with_key(self):
        items = [("b", 2), ("a", 1), ("c", 3)]
        self.assertEqual(
            heap_sort(items, key=lambda kv: -kv[1]),
            [("c", 3), ("b", 2), ("a", 1)],
        )

    def test_topk(self):
        arr = list(range(100))
        random.Random(0).shuffle(arr)
        self.assertEqual(top_k(arr, 5), [99, 98, 97, 96, 95])
        self.assertEqual(top_k(arr, 3, reverse=False), [0, 1, 2])

    def test_topk_stable_for_ties(self):
        # Quando empata, basta retornar K elementos cuja chave seja a maior.
        arr = [(i, 5) for i in range(10)]
        result = top_k(arr, 3, key=lambda kv: kv[1])
        self.assertEqual(len(result), 3)
        for _, score in result:
            self.assertEqual(score, 5)


class TestInvertedIndex(unittest.TestCase):
    def test_basic_indexing(self):
        idx = InvertedIndex()
        idx.add_document("d1", ["alpha", "beta", "alpha"])
        idx.add_document("d2", ["beta", "gamma"])
        self.assertEqual(idx.term_frequency("alpha", "d1"), 2)
        self.assertEqual(idx.term_frequency("alpha", "d2"), 0)
        self.assertEqual(idx.document_frequency("beta"), 2)
        self.assertEqual(idx.total_docs, 2)
        self.assertEqual(idx.vocabulary_size, 3)
        self.assertEqual(idx.doc_length("d1"), 3)


if __name__ == "__main__":
    unittest.main()

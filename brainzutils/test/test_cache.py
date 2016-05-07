# -*- coding: utf-8 -*-
import unittest
import datetime
from brainzutils import cache
from pymemcache.client.hash import HashClient


class CacheTestCase(unittest.TestCase):
    """Testing our custom wrapper for memcached."""
    servers = [("127.0.0.1", 11211)]
    namespace = "CB_TEST"

    def setUp(self):
        cache.init(
            servers=self.servers,
            namespace=self.namespace,
        )
        # Making sure there are no items in cache before we run each test
        cache.flush_all()

    def tearDown(self):
        cache.delete_ns_versions_dir()

    def test_init(self):
        cache.init(
            servers=[],
            namespace="TEST",
            ignore_exc=True,
        )
        self.assertFalse(cache.set("test", "Hello!"))
        self.assertFalse(cache.set("test2", {
            "one": 1,
            "two": 2,
        }))

        cache.init(
            servers=[],
            namespace="TEST",
            ignore_exc=False,
        )
        with self.assertRaises(Exception):
            cache.set("test", "Hello!")
        with self.assertRaises(Exception):
            cache.set("test2", {
                "one": 1,
                "two": 2,
            })

    def test_no_init(self):
        cache._mc = None
        with self.assertRaises(RuntimeError):
            cache.set("test", "testing")

    def test_single(self):
        self.assertTrue(cache.set("test2", "Hello!"))
        self.assertEqual(cache.get("test2"), "Hello!")

    def test_single_with_namespace(self):
        self.assertTrue(cache.set("test", 42, namespace="testing"))
        self.assertEqual(cache.get("test", namespace="testing"), 42)

    def test_single_fancy(self):
        self.assertTrue(cache.set("test3", u"Привет!"))
        self.assertEqual(cache.get("test3"), u"Привет!")

    def test_single_dict(self):
        dictionary = {
            "fancy": "yeah",
            "wow": 11,
        }
        self.assertTrue(cache.set('some_dict', dictionary))
        self.assertEqual(cache.get('some_dict'), dictionary)

    def test_single_dict_fancy(self):
        dictionary = {
            "fancy": u"Да",
            "тест": 11,
        }
        cache.set('some_dict', dictionary)
        self.assertEqual(cache.get('some_dict'), dictionary)

    def test_datetime(self):
        self.assertTrue(cache.set('some_time', datetime.datetime.now()))
        self.assertEqual(type(cache.get('some_time')), datetime.datetime)

        dictionary = {
            "id": 1,
            "created": datetime.datetime.now(),
        }
        self.assertTrue(cache.set('some_other_time', dictionary))
        self.assertEqual(cache.get('some_other_time'), dictionary)

    def test_delete(self):
        key = "testing"
        self.assertTrue(cache.set(key, u"Пример"))
        self.assertEqual(cache.get(key), u"Пример")
        self.assertTrue(cache.delete(key))
        self.assertIsNone(cache.get(key))

    def test_delete_with_namespace(self):
        key = "testing"
        namespace = "spaaaaaaace"
        self.assertTrue(cache.set(key, u"Пример", namespace=namespace))
        self.assertEqual(cache.get(key, namespace=namespace), u"Пример")
        self.assertTrue(cache.delete(key, namespace=namespace))
        self.assertIsNone(cache.get(key, namespace=namespace))

    def test_many(self):
        # With namespace
        mapping = {
            "test1": "Hello",
            "test2": "there",
        }
        self.assertTrue(cache.set_many(mapping, namespace="testing!"))
        self.assertEqual(cache.get_many(mapping.keys(), namespace="testing!"), mapping)

        # Without a namespace
        mapping = {
            "test1": "What's",
            "test2": "good",
        }
        self.assertTrue(cache.set_many(mapping))
        self.assertEqual(cache.get_many(mapping.keys()), mapping)

    def test_invalidate_namespace(self):
        namespace = "test"
        self.assertEqual(cache.invalidate_namespace(namespace), 1)
        self.assertEqual(cache.invalidate_namespace(namespace), 2)

    def test_namespace_version(self):
        name = "test"
        self.assertIsNone(cache.get_namespace_version(name))
        self.assertEqual(cache.invalidate_namespace(name), 1)
        self.assertEqual(cache.get_namespace_version(name), 1)
        self.assertEqual(cache.invalidate_namespace(name), 2)
        self.assertEqual(cache.get_namespace_version(name), 2)


class CacheBaseTestCase(unittest.TestCase):
    """Testing underlying library."""
    servers = [("127.0.0.1", 11211)]
    client = HashClient(servers)

    def setUp(self):
        # Making sure there are no items in cache before we run each test
        self.client.flush_all()

    def test_single(self):
        self.client.set('some_key', 'some value')
        result = self.client.get('some_key')
        self.assertEqual(result, b'some value')

    def test_single_int(self):
        # Note that it returns bytes even if you put an integer inside
        self.client.set('some_int', 42)
        result = self.client.get('some_int')
        self.assertEqual(result, b'42')

    def test_single_fancy(self):
        self.client.set('some_key', u'Пример'.encode(cache.CONTENT_ENCODING))
        result = self.client.get('some_key')
        self.assertEqual(result, u'Пример'.encode(cache.CONTENT_ENCODING))

    def test_single_dict(self):
        self.client.set('some_dict', {
            "fancy": "yeah",
            "wow": 11,
        })
        result = self.client.get('some_dict')
        self.assertTrue(result == b"{'wow': 11, 'fancy': 'yeah'}" or
                        result == b"{'fancy': 'yeah', 'wow': 11}")

    def test_increment(self):
        key = "key_for_testing"

        # Initially nothing
        self.assertIsNone(self.client.incr(key, 1))
        self.assertEqual(self.client.get(key), None)

        self.assertTrue(self.client.set(key, 1))
        self.assertEqual(self.client.get(key), b'1')
        self.assertTrue(self.client.incr(key, 1))
        self.assertEqual(self.client.get(key), b'2')
        self.assertTrue(self.client.incr(key, 2))
        self.assertEqual(self.client.get(key), b'4')




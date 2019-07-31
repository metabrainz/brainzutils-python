from unittest import TestCase
from mock import MagicMock
from brainzutils.musicbrainz_db.test_data import label_dreamville, label_roc_a_fella
from brainzutils.musicbrainz_db.unknown_entities import unknown_label
from brainzutils.musicbrainz_db import label as mb_label


class LabelTestCase(TestCase):

    def setUp(self):
        mb_label.mb_session = MagicMock()
        self.mock_db = mb_label.mb_session.return_value.__enter__.return_value
        self.label_query = self.mock_db.query.return_value.options.return_value.options.return_value.filter.return_value.all

    def test_get_label_by_id(self):
        self.label_query.return_value = [label_dreamville]
        label = mb_label.get_label_by_id('1aed8c3b-8e1e-46f8-b558-06357ff5f298')
        self.assertDictEqual(label, {
            "id": "1aed8c3b-8e1e-46f8-b558-06357ff5f298",
            "name": "Dreamville",
            "type": "Imprint",
            "area": "United States",
        })

    def test_fetch_multiple_labels(self):
        self.label_query.return_value = [label_dreamville, label_roc_a_fella]
        labels = mb_label.fetch_multiple_labels([
            '1aed8c3b-8e1e-46f8-b558-06357ff5f298',
            '4cccc72a-0bd0-433a-905e-dad87871397d'
        ])
        self.assertDictEqual(labels["1aed8c3b-8e1e-46f8-b558-06357ff5f298"], {
            "id": "1aed8c3b-8e1e-46f8-b558-06357ff5f298",
            "name": "Dreamville",
            "type": "Imprint",
            "area": "United States",
        })
        self.assertDictEqual(labels["4cccc72a-0bd0-433a-905e-dad87871397d"], {
            "id": "4cccc72a-0bd0-433a-905e-dad87871397d",
            "name": "Roc-A-Fella Records",
            "type": "Original Production",
            "area": "United States",
        })

    def test_fetch_multiple_labels_empty(self):
        self.label_query.return_value = []
        labels = mb_label.fetch_multiple_labels([
            '1aed8c3b-8e1e-46f8-b558-06357ff5f298',
            '4cccc72a-0bd0-433a-905e-dad87871397d'
        ], unknown_entities_for_missing=True)
        self.assertEqual(labels["1aed8c3b-8e1e-46f8-b558-06357ff5f298"]["name"], unknown_label.name)
        self.assertEqual(labels["4cccc72a-0bd0-433a-905e-dad87871397d"]["name"], unknown_label.name)

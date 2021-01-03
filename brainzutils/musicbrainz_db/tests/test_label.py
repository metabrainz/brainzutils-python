import pytest

from brainzutils.musicbrainz_db.unknown_entities import unknown_label
from brainzutils.musicbrainz_db import label as mb_label


@pytest.mark.database
class TestLabel:

    def test_get_label_by_id(self, engine):
        label = mb_label.get_label_by_id('4cccc72a-0bd0-433a-905e-dad87871397d')
        assert label == {
            "id": "4cccc72a-0bd0-433a-905e-dad87871397d",
            "name": "Roc‐A‐Fella Records",
            "type": "Original Production",
            "area": "United States",
        }

    def test_fetch_multiple_labels(self, engine):
        labels = mb_label.fetch_multiple_labels([
            'c595c289-47ce-4fba-b999-b87503e8cb71',
            '4cccc72a-0bd0-433a-905e-dad87871397d'
        ])
        assert labels["c595c289-47ce-4fba-b999-b87503e8cb71"] == {
            "id": "c595c289-47ce-4fba-b999-b87503e8cb71",
            "name": "Warner Bros. Records",
            "comment": '1958–2019; “WB” logo, with or without “records” beneath or on banner across',
            "type": "Imprint",
            "area": "United States",
        }
        assert labels["4cccc72a-0bd0-433a-905e-dad87871397d"] == {
            "id": "4cccc72a-0bd0-433a-905e-dad87871397d",
            "name": "Roc‐A‐Fella Records",
            "type": "Original Production",
            "area": "United States",
        }

    def test_fetch_multiple_labels_empty(self, engine):
        labels = mb_label.fetch_multiple_labels(['1aed8c3b-8e1e-46f8-b558-06357ff5f298'],
                                                includes=['artist-rels', 'url-rels'],
                                                unknown_entities_for_missing=True)
        assert labels["1aed8c3b-8e1e-46f8-b558-06357ff5f298"]["name"] == unknown_label.name

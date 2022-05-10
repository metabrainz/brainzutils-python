import pytest

from brainzutils.musicbrainz_db import label as mb_label


@pytest.mark.database
class TestLabel:

    def test_get_label_by_mbid(self, engine):
        label = mb_label.get_label_by_mbid('4cccc72a-0bd0-433a-905e-dad87871397d')
        assert label == {
            "mbid": "4cccc72a-0bd0-433a-905e-dad87871397d",
            "name": "Roc‐A‐Fella Records",
            "type": "Original Production",
            "area": "United States",
            "life-span": {"begin": "1996", "end": "2013"},
            "rating": 100,
        }

    def test_get_label_by_mbid_redirect(self, engine):
        label = mb_label.get_label_by_mbid('67cf4cad-c039-4f01-bc84-f8dab7791ed7')
        assert label == {
            "mbid": "50c384a2-0b44-401b-b893-8181173339c7",
            "name": "Atlantic",
            "type": "Imprint",
            "area": "United States",
            "comment": "Warner Music imprint",
            "life-span": {"begin": "1947"},
            "rating": 100,
        }

    def test_fetch_multiple_labels(self, engine):
        labels = mb_label.fetch_multiple_labels([
            'c595c289-47ce-4fba-b999-b87503e8cb71',
            '4cccc72a-0bd0-433a-905e-dad87871397d'
        ])
        assert len(labels) == 2
        assert labels["c595c289-47ce-4fba-b999-b87503e8cb71"] == {
            "mbid": "c595c289-47ce-4fba-b999-b87503e8cb71",
            "name": "Warner Bros. Records",
            "comment": '1958–2019; “WB” logo, with or without “records” beneath or on banner across',
            "type": "Imprint",
            "area": "United States",
            "life-span": {"begin": "1958-03-19", "end": "2019-05-28"},
        }
        assert labels["4cccc72a-0bd0-433a-905e-dad87871397d"] == {
            "mbid": "4cccc72a-0bd0-433a-905e-dad87871397d",
            "name": "Roc‐A‐Fella Records",
            "type": "Original Production",
            "area": "United States",
            "life-span": {"begin": "1996", "end": "2013"},
            "rating": 100
        }

    def test_fetch_multiple_labels_redirect(self, engine):
        labels = mb_label.fetch_multiple_labels([
            '67cf4cad-c039-4f01-bc84-f8dab7791ed7'
        ])
        assert len(labels) == 1
        assert labels["67cf4cad-c039-4f01-bc84-f8dab7791ed7"] == {
            "mbid": "50c384a2-0b44-401b-b893-8181173339c7",
            "name": "Atlantic",
            "type": "Imprint",
            "area": "United States",
            "comment": "Warner Music imprint",
            "life-span": {"begin": "1947"},
            "rating": 100,
        }

    def test_fetch_multiple_labels_missing(self, engine):
        labels = mb_label.fetch_multiple_labels([
            '50c384a2-0b44-401b-b893-8181173339c7',
            '50c384a2-0000-0000-0000-8181173339c7'
        ], includes=['artist-rels', 'url-rels'])
        assert list(labels.keys()) == ['50c384a2-0b44-401b-b893-8181173339c7']

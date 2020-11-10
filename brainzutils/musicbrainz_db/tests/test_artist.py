import pytest

from brainzutils.musicbrainz_db.test_data import artist_linkin_park, artist_jay_z
from brainzutils.musicbrainz_db.unknown_entities import unknown_artist
from brainzutils.musicbrainz_db import artist as mb_artist


@pytest.mark.database
class TestArtist:

    def test_get_by_id(self, engine):
        artist = mb_artist.get_artist_by_id("f59c5520-5f46-4d2c-b2c4-822eabf53419")
        assert artist == {
            "id": "f59c5520-5f46-4d2c-b2c4-822eabf53419",
            "name": "Linkin Park",
            "sort_name": "Linkin Park",
            "type": "Group"
        }

    def test_fetch_multiple_artists(self):
        self.artist_query.return_value = [artist_jay_z, artist_linkin_park]
        artists = mb_artist.fetch_multiple_artists([
            "f59c5520-5f46-4d2c-b2c4-822eabf53419",
            "f82bcf78-5b69-4622-a5ef-73800768d9ac",
        ])
        self.assertDictEqual(artists["f82bcf78-5b69-4622-a5ef-73800768d9ac"], {
            "id": "f82bcf78-5b69-4622-a5ef-73800768d9ac",
            "name": "JAY Z",
            "sort_name": "JAY Z",
            "type": "Person",
        })
        self.assertDictEqual(artists["f59c5520-5f46-4d2c-b2c4-822eabf53419"], {
            "id": "f59c5520-5f46-4d2c-b2c4-822eabf53419",
            "name": "Linkin Park",
            "sort_name": "Linkin Park",
            "type": "Group",
        })

    def test_fetch_multiple_artists_empty(self):
        self.artist_query.return_value = []
        artists = mb_artist.fetch_multiple_artists([
            "f59c5520-5f46-4d2c-b2c4-822eabf53419",
            "f82bcf78-5b69-4622-a5ef-73800768d9ac",
        ],
        includes=['artist-rels', 'url-rels'],
        unknown_entities_for_missing=True)
        self.assertEqual(artists["f82bcf78-5b69-4622-a5ef-73800768d9ac"]["name"], unknown_artist.name)
        self.assertEqual(artists["f59c5520-5f46-4d2c-b2c4-822eabf53419"]["name"], unknown_artist.name)

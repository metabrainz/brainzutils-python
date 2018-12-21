from unittest import TestCase
from mock import MagicMock
from brainzutils.musicbrainz_db.test_data import artist_linkin_park, artist_jay_z
from brainzutils.musicbrainz_db import artist as mb_artist


class ArtistTestCase(TestCase):

    def setUp(self):
        mb_artist.mb_session = MagicMock()
        self.mock_db = mb_artist.mb_session.return_value.__enter__.return_value
        self.artist_query = self.mock_db.query.return_value.options.return_value.filter.return_value.all

    def test_get_by_mbid(self):
        self.artist_query.return_value = [artist_linkin_park]
        artist = mb_artist.get_artist_by_mbid("f59c5520-5f46-4d2c-b2c4-822eabf53419", includes=["type"])
        self.assertDictEqual(artist, {
            "id": "f59c5520-5f46-4d2c-b2c4-822eabf53419",
            "name": "Linkin Park",
            "sort_name": "Linkin Park",
            "type": "Group"
        })

    def test_fetch_multiple_artists(self):
        self.artist_query.return_value = [artist_jay_z, artist_linkin_park]
        artists = mb_artist._fetch_multiple_artists([
            "f59c5520-5f46-4d2c-b2c4-822eabf53419",
            "f82bcf78-5b69-4622-a5ef-73800768d9ac",
        ], includes=["type"])
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

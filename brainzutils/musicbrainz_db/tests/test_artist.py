import pytest

from brainzutils.musicbrainz_db import artist as mb_artist


@pytest.mark.database
class TestArtist:

    def test_get_artist_by_mbid(self, engine):
        artist = mb_artist.get_artist_by_mbid("f59c5520-5f46-4d2c-b2c4-822eabf53419")
        assert artist == {
            "mbid": "f59c5520-5f46-4d2c-b2c4-822eabf53419",
            "name": "Linkin Park",
            "sort_name": "Linkin Park",
            "comment": "American rock band",
            "life-span": {"begin": "1999"},
            "rating": 85,
            "type": "Group",
        }

    def test_get_artist_by_mbid_redirect(self, engine):
        """Using an MBID which is a redirect will return the "canonical" id"""
        artist = mb_artist.get_artist_by_mbid("b3d01315-d52a-4f3a-908b-0618315c1ef2")
        assert artist == {
            "mbid": "79239441-bfd5-4981-a70c-55c3f15c1287",
            "name": "Madonna",
            "sort_name": "Madonna",
            "comment": "“Queen of Pop”",
            "life-span": {"begin": "1958-08-16"},
            "rating": 88,
            "type": "Person",
        }

    def test_fetch_multiple_artists(self, engine):
        artists = mb_artist.fetch_multiple_artists([
            "f59c5520-5f46-4d2c-b2c4-822eabf53419",
            "f82bcf78-5b69-4622-a5ef-73800768d9ac",
        ])
        assert artists["f82bcf78-5b69-4622-a5ef-73800768d9ac"] == {
            "mbid": "f82bcf78-5b69-4622-a5ef-73800768d9ac",
            "name": "JAY‐Z",
            "sort_name": "JAY‐Z",
            "type": "Person",
            "comment": "US rapper",
            "life-span": {"begin": "1969-12-04"},
            "rating": 71,
        }
        assert artists["f59c5520-5f46-4d2c-b2c4-822eabf53419"] == {
            "mbid": "f59c5520-5f46-4d2c-b2c4-822eabf53419",
            "name": "Linkin Park",
            "sort_name": "Linkin Park",
            "type": "Group",
            "comment": "American rock band",
            "life-span": {"begin": "1999"},
            "rating": 85,
        }

    def test_fetch_multiple_artists_redirect(self, engine):
        """Artist with a redirect uses redirected mbid in dictionary key, but canonical id in returned data"""
        artists = mb_artist.fetch_multiple_artists(["fe008f22-07be-46f0-9206-7cab2d26e89d"])
        assert len(artists) == 1
        assert artists["fe008f22-07be-46f0-9206-7cab2d26e89d"] == {
            "mbid": "f59c5520-5f46-4d2c-b2c4-822eabf53419",
            "name": "Linkin Park",
            "sort_name": "Linkin Park",
            "comment": "American rock band",
            "life-span": {"begin": "1999"},
            "rating": 85,
            "type": "Group"
        }

    def test_fetch_multiple_artists_missing(self, engine):
        """If an artist id doesn't exist, don't fetch it"""
        artists = mb_artist.fetch_multiple_artists(["f59c5520-5f46-4d2c-b2c4-822eabf53419",
                                                    "f59c5520-aaaa-aaaa-b2c4-822eabf53419"],
                                                   includes=['artist-rels', 'url-rels'])
        assert list(artists.keys()) == ["f59c5520-5f46-4d2c-b2c4-822eabf53419"]

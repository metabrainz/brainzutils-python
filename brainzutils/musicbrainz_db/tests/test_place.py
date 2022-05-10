import pytest

from brainzutils.musicbrainz_db import place as mb_place


@pytest.mark.database
class TestPlace:

    def test_get_place_by_mbid(self, engine):
        place = mb_place.get_place_by_mbid('4352063b-a833-421b-a420-e7fb295dece0')
        assert place['name'] == 'Royal Albert Hall'
        assert place['type'] == 'Venue'
        assert place['coordinates'] == {
            'latitude': 51.50105,
            'longitude': -0.17748
        }
        assert place['area'] == {
            'mbid': 'b9576171-3434-4d1b-8883-165ed6e65d2f',
            'name': 'Kensington and Chelsea',
        }

    def test_get_place_by_mbid_redirect(self, engine):
        place = mb_place.get_place_by_mbid('b1690ae6-5a37-46d7-99ae-b7e2d790485f')
        assert place == {
            'address': 'Herbert-von-Karajan-Straße 1, 10785 Berlin, Germany',
            'area': {'mbid': 'c9ac1239-e832-41bc-9930-e252a1fd1105', 'name': 'Berlin'},
            'coordinates': {'latitude': 52.51, 'longitude': 13.37},
            'mbid': 'bea135c0-a32e-49be-85fd-9234c73fa0a8',
            'name': 'Berliner Philharmonie',
            'type': 'Venue',
            'life-span': {'begin': '1963'},
        }

    def test_fetch_multiple_places(self, engine):
        places = mb_place.fetch_multiple_places(
            ['4352063b-a833-421b-a420-e7fb295dece0', '2056ad56-cea9-4536-9f2d-58765a38829c']
        )
        assert places['4352063b-a833-421b-a420-e7fb295dece0']['name'] == 'Royal Albert Hall'
        assert places['2056ad56-cea9-4536-9f2d-58765a38829c']['name'] == 'Finnvox'

    def test_fetch_multiple_places_redirect(self, engine):
        places = mb_place.fetch_multiple_places(
            ['4352063b-a833-421b-a420-e7fb295dece0', 'b1690ae6-5a37-46d7-99ae-b7e2d790485f']
        )
        assert len(places) == 2
        assert places['b1690ae6-5a37-46d7-99ae-b7e2d790485f']['mbid'] == 'bea135c0-a32e-49be-85fd-9234c73fa0a8'
        assert places['b1690ae6-5a37-46d7-99ae-b7e2d790485f']['name'] == 'Berliner Philharmonie'

    def test_fetch_multiple_places_empty(self, engine):
        places = mb_place.fetch_multiple_places(
            ['bea135c0-a32e-49be-85fd-9234c73fa0a8', 'bea135c0-3333-3333-3333-9234c73fa0a8'],
            includes=['artist-rels', 'place-rels', 'url-rels']
        )
        assert list(places.keys()) == ['bea135c0-a32e-49be-85fd-9234c73fa0a8']

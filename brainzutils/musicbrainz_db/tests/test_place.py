import pytest

from brainzutils.musicbrainz_db import place as mb_place
from brainzutils.musicbrainz_db.unknown_entities import unknown_place


@pytest.mark.database
class TestPlace:

    def test_get_by_id(self, engine):
        place = mb_place.get_place_by_id('4352063b-a833-421b-a420-e7fb295dece0')
        assert place['name'] == 'Royal Albert Hall'
        assert place['type'] == 'Venue'
        assert place['coordinates'] == {
            'latitude': 51.50105,
            'longitude': -0.17748
        }
        assert place['area'] == {
            'id': 'b9576171-3434-4d1b-8883-165ed6e65d2f',
            'name': 'Kensington and Chelsea',
        }

    def test_fetch_multiple_places(self, engine):
        places = mb_place.fetch_multiple_places(
            ['4352063b-a833-421b-a420-e7fb295dece0', '2056ad56-cea9-4536-9f2d-58765a38829c']
        )
        assert places['4352063b-a833-421b-a420-e7fb295dece0']['name'] == 'Royal Albert Hall'
        assert places['2056ad56-cea9-4536-9f2d-58765a38829c']['name'] == 'Finnvox Studios'

    def test_fetch_multiple_places_empty(self, engine):
        places = mb_place.fetch_multiple_places(
            ['f9587914-8505-4bd1-833b-16a3100a4948', 'd71ffe38-5eaf-426b-9a2e-e1f21bc84609'],
            includes=['artist-rels', 'place-rels', 'url-rels'],
            unknown_entities_for_missing=True
        )
        assert places['d71ffe38-5eaf-426b-9a2e-e1f21bc84609']['name'] == unknown_place.name
        assert places['f9587914-8505-4bd1-833b-16a3100a4948']['name'] == unknown_place.name

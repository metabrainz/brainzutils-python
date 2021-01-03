import pytest

from brainzutils.musicbrainz_db import event as mb_event
from brainzutils.musicbrainz_db.unknown_entities import unknown_event


@pytest.mark.database
class TestEvent:

    def test_get_event_by_id(self, engine):
        event = mb_event.get_event_by_id('d4921d43-bf92-464e-aef4-bba8540fc5bd')
        assert event == {
            'id': 'd4921d43-bf92-464e-aef4-bba8540fc5bd',
            'name': 'Butterfly Whirl 2015',
        }

    def test_fetch_multiple_events(self, engine):
        events = mb_event.fetch_multiple_events(
            ['d4921d43-bf92-464e-aef4-bba8540fc5bd', 'b335b093-b3a0-411f-9f3d-7f680a4992d6'],
        )
        assert events['d4921d43-bf92-464e-aef4-bba8540fc5bd']['name'] == 'Butterfly Whirl 2015'
        assert events['b335b093-b3a0-411f-9f3d-7f680a4992d6']['name'] == 'KISS in Atlanta'

    def test_fetch_multiple_events_empty(self, engine):
        events = mb_event.fetch_multiple_events([
            'ebe6ce0f-22c0-4fe7-bfd4-7a0397c9fe94',
            '40e6153d-a042-4c95-a0a9-b0a47e3825ce'
        ],
            includes=['artist-rels', 'place-rels', 'series-rels', 'url-rels', 'release-group-rels'],
            unknown_entities_for_missing=True)
        assert events['ebe6ce0f-22c0-4fe7-bfd4-7a0397c9fe94']['name'] == unknown_event.name
        assert events['40e6153d-a042-4c95-a0a9-b0a47e3825ce']['name'] == unknown_event.name

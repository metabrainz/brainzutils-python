import pytest

from brainzutils.musicbrainz_db import event as mb_event


@pytest.mark.database
class TestEvent:

    def test_get_event_by_mbid(self, engine):
        event = mb_event.get_event_by_mbid('d4921d43-bf92-464e-aef4-bba8540fc5bd')
        assert event == {
            'mbid': 'd4921d43-bf92-464e-aef4-bba8540fc5bd',
            'name': 'Butterfly Whirl 2015',
            'life-span': {'begin': '2015-05-22', 'end': '2015-05-25'},
        }

    def test_get_event_by_mbid_redirect(self, engine):
        """If using an id that is redirected, return the """
        event = mb_event.get_event_by_mbid('b8528315-ef77-46e2-bff9-d1b00d84dc3f')
        assert event == {
            'mbid': '499559c8-b84b-422e-8ad7-b746d48c21aa',
            'name': '1995-10-11: Riverport Amphitheatre, Maryland Heights, Missouri',
            'life-span': {'begin': '1995-10-11', 'end': '1995-10-11'},
            'rating': 100,
        }

    def test_fetch_multiple_events(self, engine):
        events = mb_event.fetch_multiple_events(
            ['d4921d43-bf92-464e-aef4-bba8540fc5bd', 'b335b093-b3a0-411f-9f3d-7f680a4992d6'],
        )
        assert events['d4921d43-bf92-464e-aef4-bba8540fc5bd']['name'] == 'Butterfly Whirl 2015'
        assert events['b335b093-b3a0-411f-9f3d-7f680a4992d6']['name'] == 'KISS in Atlanta'

    def test_fetch_multiple_events_redirect(self, engine):
        """"""
        events = mb_event.fetch_multiple_events(
            ['b8528315-ef77-46e2-bff9-d1b00d84dc3f'],
        )
        assert events == {'b8528315-ef77-46e2-bff9-d1b00d84dc3f': {
            'mbid': '499559c8-b84b-422e-8ad7-b746d48c21aa',
            'name': '1995-10-11: Riverport Amphitheatre, Maryland Heights, Missouri',
            'life-span': {'begin': '1995-10-11', 'end': '1995-10-11'},
            'rating': 100,
        }}

    def test_fetch_multiple_events_empty(self, engine):
        """If an event id doesn't exist, don't return it in the list"""
        events = mb_event.fetch_multiple_events([
            'd4921d43-bf92-464e-aef4-bba8540fc5bd',
            '40e6153d-4444-4444-4444-b0a47e3825ce'
        ],
            includes=['artist-rels', 'place-rels', 'series-rels', 'url-rels', 'release-group-rels'])
        assert list(events.keys()) == ['d4921d43-bf92-464e-aef4-bba8540fc5bd']

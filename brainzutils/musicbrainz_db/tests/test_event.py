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
            'type': 'Festival'
        }

    def test_get_event_by_mbid_redirect(self, engine):
        """If using an id that is redirected, return the """
        event = mb_event.get_event_by_mbid('b8528315-ef77-46e2-bff9-d1b00d84dc3f')
        assert event == {
            'mbid': '499559c8-b84b-422e-8ad7-b746d48c21aa',
            'name': '1995-10-11: Riverport Amphitheatre, Maryland Heights, Missouri',
            'life-span': {'begin': '1995-10-11', 'end': '1995-10-11'},
            'rating': 100,
            'type': 'Concert',
        }

    def test_get_event_by_mbid_with_includes(self, engine):
        event = mb_event.get_event_by_mbid('b8528315-ef77-46e2-bff9-d1b00d84dc3f',
            includes=['artist-rels'])
        assert event['mbid'] == '499559c8-b84b-422e-8ad7-b746d48c21aa'
        assert len(event['artist-rels']) == 1
        assert event['artist-rels'][0]['type-id'] == '936c7c95-3156-3889-a062-8a0cd57f8946'

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
            'type': 'Concert',
        }}

    def test_fetch_multiple_events_empty(self, engine):
        """If an event id doesn't exist, don't return it in the list"""
        events = mb_event.fetch_multiple_events([
            'd4921d43-bf92-464e-aef4-bba8540fc5bd',
            '40e6153d-4444-4444-4444-b0a47e3825ce'
        ],
            includes=['artist-rels', 'place-rels', 'series-rels', 'url-rels', 'release-group-rels'])
        assert list(events.keys()) == ['d4921d43-bf92-464e-aef4-bba8540fc5bd']

    def test_get_events_for_place(self, engine):
        events = mb_event.get_events_for_place(
            place_id='4352063b-a833-421b-a420-e7fb295dece0',
            event_types=['Concert', 'Festival'],
            include_null_type=False,
        )
        assert events[0][0] == {
            "life-span": {
                "begin": "2015-07-17",
                "end": "2015-09-12"
            },
            "mbid": "00d6449e-c6d2-42f1-a09e-c01668af1dd7",
            "name": "The Proms 2015",
            "type": "Festival"
        }

        assert events[1] == 5
        assert len(events[0]) == 5

        events2 = mb_event.get_events_for_place(
            place_id='06e5431e-ef98-424c-a43a-4b7a3cf26327',
            event_types=[],
            include_null_type=True,
        )

        # first item doesn't have a 'type' key
        assert events2[0][0] == {
            "life-span": {
                "begin": "2015-12-19",
                "end": "2015-12-19"
            },
            "mbid": "6cc3999a-2f19-433e-b760-f2ff2a6bc86b",
            "name": "2015-12-19: Studio 8H, GE Building, Rockefeller Center, New York City, NY, USA",
            'comment': 'Saturday Night Live',
        }

        assert events2[1] == 5

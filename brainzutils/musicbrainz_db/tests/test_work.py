from unittest import TestCase
from mock import MagicMock
from brainzutils.musicbrainz_db.test_data import work_a_lot, work_aquemini
from brainzutils.musicbrainz_db.unknown_entities import unknown_work
from brainzutils.musicbrainz_db import work as mb_work


class WorkTestCase(TestCase):

    def setUp(self):
        mb_work.mb_session = MagicMock()
        self.mock_db = mb_work.mb_session.return_value.__enter__.return_value
        self.work_query = self.mock_db.query.return_value.options.return_value.filter.return_value.all

    def test_get_work_by_id(self):
        self.work_query.return_value = [work_a_lot]
        work = mb_work.get_work_by_id('54ce5e07-2aca-4578-83d8-5a41a7b2f434')
        self.assertDictEqual(work, {
            "id": "54ce5e07-2aca-4578-83d8-5a41a7b2f434",
            "name": "a lot",
            "type": "Song",
        })

    def test_fetch_multiple_works(self):
        self.work_query.return_value = [work_a_lot, work_aquemini]
        works = mb_work.fetch_multiple_works([
            '54ce5e07-2aca-4578-83d8-5a41a7b2f434',
            '757504fb-a130-4b84-9eb5-1b37164f12dd'
        ])
        self.assertDictEqual(works["54ce5e07-2aca-4578-83d8-5a41a7b2f434"], {
            "id": "54ce5e07-2aca-4578-83d8-5a41a7b2f434",
            "name": "a lot",
            "type": "Song",
        })
        self.assertDictEqual(works["757504fb-a130-4b84-9eb5-1b37164f12dd"], {
            "id": "757504fb-a130-4b84-9eb5-1b37164f12dd",
            "name": "Aquemini",
            "type": "Song",
        })

    def test_fetch_multiple_works_empty(self):
        self.work_query.return_value = []
        works = mb_work.fetch_multiple_works([
            '54ce5e07-2aca-4578-83d8-5a41a7b2f434',
            '757504fb-a130-4b84-9eb5-1b37164f12dd'
        ], unknown_entities_for_missing=True)
        self.assertEqual(works["54ce5e07-2aca-4578-83d8-5a41a7b2f434"]["name"], unknown_work.name)
        self.assertEqual(works["757504fb-a130-4b84-9eb5-1b37164f12dd"]["name"], unknown_work.name)

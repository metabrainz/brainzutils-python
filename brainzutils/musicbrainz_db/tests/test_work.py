import pytest

from brainzutils.musicbrainz_db.unknown_entities import unknown_work
from brainzutils.musicbrainz_db import work as mb_work


@pytest.mark.database
class TestWork:

    def test_get_work_by_id(self):
        work = mb_work.get_work_by_id('d35f8fb8-52ab-4a12-b1c8-f2054d10cf88')
        assert work == {
            "id": "d35f8fb8-52ab-4a12-b1c8-f2054d10cf88",
            "name": "Apple Bush",
            "type": "Song",
        }

    def test_fetch_multiple_works(self):
        works = mb_work.fetch_multiple_works([
            'd35f8fb8-52ab-4a12-b1c8-f2054d10cf88',
            '1deb7377-f980-4adb-8f0f-a36355461f38'
        ])
        assert works["d35f8fb8-52ab-4a12-b1c8-f2054d10cf88"] == {
            "id": "d35f8fb8-52ab-4a12-b1c8-f2054d10cf88",
            "name": "Apple Bush",
            "type": "Song",
        }
        assert works["1deb7377-f980-4adb-8f0f-a36355461f38"] == {
            "id": "1deb7377-f980-4adb-8f0f-a36355461f38",
            "name": "Fields of Regret",
            "type": "Song",
        }

    def test_fetch_multiple_works_empty(self):
        works = mb_work.fetch_multiple_works([
            '54ce5e07-2aca-4578-83d8-5a41a7b2f434',
            '757504fb-a130-4b84-9eb5-1b37164f12dd'
        ],
            includes=['artist-rels', 'recording-rels'],
            unknown_entities_for_missing=True)
        assert works["54ce5e07-2aca-4578-83d8-5a41a7b2f434"]["name"] == unknown_work.name
        assert works["757504fb-a130-4b84-9eb5-1b37164f12dd"]["name"] == unknown_work.name

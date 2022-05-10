import pytest

from brainzutils.musicbrainz_db import work as mb_work


@pytest.mark.database
class TestWork:
    def test_get_work_by_mbid(self, engine):
        work = mb_work.get_work_by_mbid('d35f8fb8-52ab-4a12-b1c8-f2054d10cf88')
        assert work == {
            "mbid": "d35f8fb8-52ab-4a12-b1c8-f2054d10cf88",
            "name": "Apple Bush",
            "type": "Song",
        }

    def test_get_work_by_mbid_redirect(self, engine):
        work = mb_work.get_work_by_mbid('4531bed5-073c-37a8-9500-70de8583c0a1')
        assert work == {
            "mbid": "36e33f94-ef5f-36b5-97b0-c1ed9c5a542f",
            "name": "Jesus Walks",
            "type": "Song",
        }

    def test_get_work_by_mbid_with_includes(self, engine):
        work = mb_work.get_work_by_mbid('4531bed5-073c-37a8-9500-70de8583c0a1',
            includes=['artist-rels', 'recording-rels'])
        assert work["mbid"] == "36e33f94-ef5f-36b5-97b0-c1ed9c5a542f"
        assert len(work["artist-rels"]) == 4
        assert len(work["recording-rels"]) == 55

    def test_fetch_multiple_works(self, engine):
        works = mb_work.fetch_multiple_works([
            'd35f8fb8-52ab-4a12-b1c8-f2054d10cf88',
            '1deb7377-f980-4adb-8f0f-a36355461f38'
        ])
        assert works["d35f8fb8-52ab-4a12-b1c8-f2054d10cf88"] == {
            "mbid": "d35f8fb8-52ab-4a12-b1c8-f2054d10cf88",
            "name": "Apple Bush",
            "type": "Song",
        }
        assert works["1deb7377-f980-4adb-8f0f-a36355461f38"] == {
            "mbid": "1deb7377-f980-4adb-8f0f-a36355461f38",
            "name": "Fields of Regret",
            "type": "Song",
        }

    def test_fetch_multiple_works_redirect(self, engine):
        works = mb_work.fetch_multiple_works([
            '4531bed5-073c-37a8-9500-70de8583c0a1',
        ])
        assert works == {
            '4531bed5-073c-37a8-9500-70de8583c0a1': {
                "mbid": "36e33f94-ef5f-36b5-97b0-c1ed9c5a542f",
                "name": "Jesus Walks",
                "type": "Song",
            }
        }

    def test_fetch_multiple_works_missing(self, engine):
        works = mb_work.fetch_multiple_works([
            '36e33f94-ef5f-36b5-97b0-c1ed9c5a542f',
            '36e33f94-eeee-eeee-eeee-c1ed9c5a542f'
        ])
        assert list(works.keys()) == ['36e33f94-ef5f-36b5-97b0-c1ed9c5a542f']

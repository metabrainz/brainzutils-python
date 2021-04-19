import pytest

from brainzutils.musicbrainz_db import recording as mb_recording


@pytest.mark.database
class TestRecording:

    def test_get_recording_by_mbid(self, engine):
        """ Tests if appropriate recording is returned for a given MBID. """
        recording = mb_recording.get_recording_by_mbid('daccb724-8023-432a-854c-e0accb6c8678', includes=['artists'])

        assert recording == {
            'id': 'daccb724-8023-432a-854c-e0accb6c8678',
            'name': 'Numb / Encore',
            'comment': 'explicit',
            'length': 205.28,
            'artist-credit-phrase': 'Jay-Z / Linkin Park',
            'artists': [
                {
                    'id': 'f82bcf78-5b69-4622-a5ef-73800768d9ac',
                    'name': 'JAY‐Z',
                    'credited_name': 'Jay-Z',
                    'join_phrase': ' / '
                },
                {
                    'id': 'f59c5520-5f46-4d2c-b2c4-822eabf53419',
                    'name': 'Linkin Park'
                }
            ]
        }

    def test_get_recording_by_mbid_redirect(self, engine):
        recording = mb_recording.get_recording_by_mbid('e00d4dce-097e-4098-bbb3-77db884566f3')
        assert recording == {
            'id': 'fbe3d0b9-3990-4a76-bddb-12f4a0447a2c',
            'name': 'The Perfect Drug (Nine Inch Nails)',
            'length': 499
        }

    def test_fetch_multiple_recordings(self, engine):
        """ Tests if appropriate recordings are returned for a given list of MBIDs. """

        mbids = ['daccb724-8023-432a-854c-e0accb6c8678', 'ae83579c-5f33-4a35-83f3-89206c44a426']
        recordings = mb_recording.fetch_multiple_recordings(mbids, includes=['artists'])

        assert recordings == {
            'daccb724-8023-432a-854c-e0accb6c8678': {
                'id': 'daccb724-8023-432a-854c-e0accb6c8678',
                'name': 'Numb / Encore',
                'comment': 'explicit',
                'length': 205.28,
                'artist-credit-phrase': 'Jay-Z / Linkin Park',
                'artists': [
                    {
                        'id': 'f82bcf78-5b69-4622-a5ef-73800768d9ac',
                        'name': 'JAY‐Z',
                        'credited_name': 'Jay-Z',
                        'join_phrase': ' / '
                    },
                    {
                        'id': 'f59c5520-5f46-4d2c-b2c4-822eabf53419',
                        'name': 'Linkin Park'
                    }
                ]
            },
            'ae83579c-5f33-4a35-83f3-89206c44a426': {
                'id': 'ae83579c-5f33-4a35-83f3-89206c44a426',
                'name': "I'm a Stranger Here Myself",
                'length': 344.0,
                'artist-credit-phrase': 'Charlie Byrd & The Washington Guitar Quintet',
                'artists': [
                    {
                        'id': '9d99c378-247c-47a3-94ea-753efa330023',
                        'name': 'Charlie Byrd',
                        'join_phrase': ' & '
                    },
                    {
                        'id': 'c805fb7e-c8ff-49e0-b74f-61d638444fad',
                        'name': 'The Washington Guitar Quintet'
                    }
                ]
            }
        }

    def test_fetch_multiple_recordings_redirect(self, engine):
        recordings = mb_recording.fetch_multiple_recordings([
            'e00d4dce-097e-4098-bbb3-77db884566f3'
        ])
        assert recordings == {
            'e00d4dce-097e-4098-bbb3-77db884566f3': {
                'id': 'fbe3d0b9-3990-4a76-bddb-12f4a0447a2c',
                'name': 'The Perfect Drug (Nine Inch Nails)',
                'length': 499
            }
        }

    def test_fetch_multiple_recordings_missing(self, engine):
        """ Tests if appropriate recordings are returned for a given list of MBIDs. """

        recordings = mb_recording.fetch_multiple_recordings(
            ['e00d4dce-097e-4098-bbb3-77db884566f3', 'e00d4dce-0000-0000-0000-77db884566f3']
        )

        assert list(recordings.keys()) == ['e00d4dce-097e-4098-bbb3-77db884566f3']

# -*- coding: utf-8 -*-

import pytest

from brainzutils.musicbrainz_db import recording as mb_recording
from brainzutils.musicbrainz_db.unknown_entities import unknown_recording


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

    def test_fetch_multiple_recordings_empty(self, engine):
        """ Tests if appropriate recordings are returned for a given list of MBIDs. """

        mbids = ['daccb724-8023-0000-0000-e0accb6c8678', '965b75df-397d-4395-aac8-de11854c4630']
        recordings = mb_recording.fetch_multiple_recordings(
            mbids,
            includes=['artists', 'url-rels', 'work-rels'],
            unknown_entities_for_missing=True
        )

        assert recordings['daccb724-8023-0000-0000-e0accb6c8678']['name'] == unknown_recording.name
        assert recordings['965b75df-397d-4395-aac8-de11854c4630']['name'] == unknown_recording.name

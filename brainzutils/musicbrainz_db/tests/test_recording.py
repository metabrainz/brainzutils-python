from brainzutils.musicbrainz_db import recording as mb_recording
from brainzutils.musicbrainz_db.serialize import serialize_recording 
from brainzutils.musicbrainz_db.unknown_entities import unknown_recording
from brainzutils.musicbrainz_db.test_data import recording_numb_encore_explicit, recording_numb_encore_instrumental
from unittest import TestCase
from mock import MagicMock


class RecordingTestCase(TestCase):

    def setUp(self):
        mb_recording.mb_session = MagicMock()
        self.mock_db = mb_recording.mb_session.return_value.__enter__.return_value
        self.recording_query = self.mock_db.query.return_value.options.return_value.\
            options.return_value.options.return_value.filter.return_value.all

    def test_get_recording_by_mbid(self):
        """ Tests if appropriate recording is returned for a given MBID. """

        self.recording_query.return_value = [recording_numb_encore_explicit]
        recording = mb_recording.get_recording_by_mbid('daccb724-8023-432a-854c-e0accb6c8678', includes=['artists'])

        self.assertDictEqual(recording,
            {
                'id': 'daccb724-8023-432a-854c-e0accb6c8678',
                'name': 'Numb/Encore (explicit)',
                'length': 205.28,
                'artists':[
                    {
                        'id': 'f82bcf78-5b69-4622-a5ef-73800768d9ac',
                        'name': 'JAY Z',
                        'credited_name': 'Jay-Z',
                        'join_phrase': '/'
                    },
                    {
                        'id': 'f59c5520-5f46-4d2c-b2c4-822eabf53419',
                        'name': 'Linkin Park'
                    }
                ]
            }
        )
    
    def test_fetch_multiple_recordings(self):
        """ Tests if appropriate recordings are returned for a given list of MBIDs. """

        self.recording_query.return_value = [recording_numb_encore_explicit, 
            recording_numb_encore_instrumental]

        mbids = ['daccb724-8023-432a-854c-e0accb6c8678', '965b75df-397d-4395-aac8-de11854c4630']
        recordings = mb_recording.fetch_multiple_recordings(mbids, includes=['artists'])

        self.assertDictEqual(recordings,
            {
                'daccb724-8023-432a-854c-e0accb6c8678': 
                    {
                        'id': 'daccb724-8023-432a-854c-e0accb6c8678',
                        'name': 'Numb/Encore (explicit)',
                        'length': 205.28, 
                        'artists':
                            [
                                {'id': 'f82bcf78-5b69-4622-a5ef-73800768d9ac',
                                    'name': 'JAY Z', 'credited_name': 'Jay-Z',
                                    'join_phrase': '/'
                                },
                                {
                                    'id': 'f59c5520-5f46-4d2c-b2c4-822eabf53419',
                                    'name': 'Linkin Park'
                                }
                            ]
                    },
                '965b75df-397d-4395-aac8-de11854c4630':
                    {
                        'id': '965b75df-397d-4395-aac8-de11854c4630',
                        'name': 'Numb/Encore (instrumental)',
                        'length': 207.333,
                        'artists': 
                            [
                                {
                                    'id': 'f82bcf78-5b69-4622-a5ef-73800768d9ac',
                                    'name': 'JAY Z',
                                    'credited_name': 'Jay-Z',
                                    'join_phrase': '/'
                                },
                                {
                                    'id': 'f59c5520-5f46-4d2c-b2c4-822eabf53419',
                                    'name': 'Linkin Park'
                                }
                            ]
                    }
            }
        )

    def test_fetch_multiple_recordings_empty(self):
        """ Tests if appropriate recordings are returned for a given list of MBIDs. """

        self.recording_query.return_value = []

        mbids = ['daccb724-8023-432a-854c-e0accb6c8678', '965b75df-397d-4395-aac8-de11854c4630']
        recordings = mb_recording.fetch_multiple_recordings(mbids, includes=['artists'], unknown_entities_for_missing=True)

        self.assertEqual(recordings['daccb724-8023-432a-854c-e0accb6c8678']['name'], unknown_recording.name)
        self.assertEqual(recordings['965b75df-397d-4395-aac8-de11854c4630']['name'], unknown_recording.name)

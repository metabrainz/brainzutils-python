from datetime import datetime, date

from brainzutils.musicbrainz_db.serialize import serialize_recording, serialize_artist_credit, serialize_editor
from brainzutils.musicbrainz_db.test_data import recording_numb_encore_explicit, artistcredit_jay_z_linkin_park, \
    editor_2
from unittest import TestCase


class SerializeTestCase(TestCase):
    def test_serialize_recording(self):
        """Tests that recordings are serialized properly."""
        # Without any includes
        recording = serialize_recording(recording_numb_encore_explicit)
        self.assertDictEqual(recording,
                             {
                                 'length': 205.28,
                                 'mbid': 'daccb724-8023-432a-854c-e0accb6c8678',
                                 'name': 'Numb/Encore (explicit)',
                             }
                             )

        # With artists included
        artists = recording_numb_encore_explicit.artist_credit.artists
        recording = serialize_recording(
            recording_numb_encore_explicit,
            includes={'artists': artists, 'artist-credit-phrase': 'Jay-Z/Linkin Park'}
        )
        self.assertDictEqual(recording,
                             {
                                 'mbid': 'daccb724-8023-432a-854c-e0accb6c8678',
                                 'name': 'Numb/Encore (explicit)',
                                 'length': 205.28,
                                 'artist-credit-phrase': 'Jay-Z/Linkin Park',
                                 'artists': [
                                     {
                                         'mbid': 'f82bcf78-5b69-4622-a5ef-73800768d9ac',
                                         'name': 'JAY Z',
                                         'credited_name': 'Jay-Z',
                                         'join_phrase': '/'
                                     },
                                     {
                                         'mbid': 'f59c5520-5f46-4d2c-b2c4-822eabf53419',
                                         'name': 'Linkin Park'
                                     }
                                 ]
                             }
                             )

    def test_serialize_artist_credits(self):
        """Test that artist_credits are serialized properly."""
        artist_credits = serialize_artist_credit(artistcredit_jay_z_linkin_park)
        self.assertListEqual(artist_credits,
                             [
                                 {
                                     'mbid': 'f82bcf78-5b69-4622-a5ef-73800768d9ac',
                                     'name': 'JAY Z',
                                     'credited_name': 'Jay-Z',
                                     'join_phrase': '/'
                                 },
                                 {
                                     'mbid': 'f59c5520-5f46-4d2c-b2c4-822eabf53419',
                                     'name': 'Linkin Park'
                                 }
                             ]
                             )

    def test_serialize_editor(self):
        """Test that sensitive information is removed, everything else is covered in test_editor."""
        editor = serialize_editor(editor_2)
        self.assertNotIn("password", editor)
        self.assertNotIn("ha1", editor)
        self.assertEqual(editor, {
            'id': 2324,
            'name': 'Editor 2',
            'privs': 3,
            'email': 'editor@example.com',
            'website': 'example.com',
            'bio': 'Random\neditor',
            'member_since': datetime(2014, 12, 1, 14, 6, 42, 321443),
            'email_confirm_date': datetime(2014, 12, 1, 14, 6, 42, 321443),
            'last_login_date': datetime(2014, 12, 1, 14, 6, 42, 321443),
            'last_updated': datetime(2014, 12, 1, 14, 6, 42, 321443),
            'birth_date': date(1999, 1, 1),
            'deleted': False,
            'gender': None,
            'area': {
                "mbid": "4479c385-74d8-4a2b-bdab-f48d1e6969ba",
                "name": "Hämeenlinna"
            }
        })

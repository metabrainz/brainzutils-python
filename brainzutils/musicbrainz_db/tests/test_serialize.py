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
                                 'id': 'daccb724-8023-432a-854c-e0accb6c8678',
                                 'name': 'Numb/Encore (explicit)',
                             }
                             )

        # With artists included
        recording = serialize_recording(recording_numb_encore_explicit, includes={'artists'})
        self.assertDictEqual(recording,
                             {
                                 'id': 'daccb724-8023-432a-854c-e0accb6c8678',
                                 'name': 'Numb/Encore (explicit)',
                                 'length': 205.28,
                                 'artists': [
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

    def test_serialize_artist_credits(self):
        """Test that artist_credits are serialized properly."""
        artist_credits = serialize_artist_credit(artistcredit_jay_z_linkin_park)
        self.assertListEqual(artist_credits,
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
                             )

    def test_serialize_editor(self):
        """Test that sensitive information is removed, everything else is covered in test_editor."""
        editor = serialize_editor(editor_2)
        self.assertNotIn("password", editor)
        self.assertNotIn("ha1", editor)

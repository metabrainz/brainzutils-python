from unittest import TestCase
from mock import MagicMock
from brainzutils.musicbrainz_db.test_data import editor_dt, editor_date, editor_1, editor_2
from brainzutils.musicbrainz_db import editor as mb_editor


class EditorTestCase(TestCase):
    def setUp(self):
        mb_editor.mb_session = MagicMock()
        self.mock_db = mb_editor.mb_session.return_value.__enter__.return_value
        self.editor_query = self.mock_db.query.return_value.filter.return_value.all

        self.editor_1_dict = {
            "id": 2323,
            "name": "Editor 1",
            "privs": 0,
            "email": None,
            "website": None,
            "bio": None,
            "member_since": editor_dt,
            "email_confirm_date": editor_dt,
            "last_login_date": editor_dt,
            "last_updated": editor_dt,
            "birth_date": None,
            "deleted": False,
            "gender": None,
            "area": None,
        }

        self.editor_2_dict = {
            "id": 2324,
            "name": "Editor 2",
            "privs": 3,
            "email": "editor@example.com",
            "website": "example.com",
            "bio": "Random\neditor",
            "member_since": editor_dt,
            "email_confirm_date": editor_dt,
            "last_login_date": editor_dt,
            "last_updated": editor_dt,
            "birth_date": editor_date,
            "deleted": False,
            "gender": None,
            "area": None,
        }

    def test_get_by_id(self):
        self.editor_query.return_value = [editor_1]
        editor = mb_editor.get_editor_by_id(2323)
        self.assertDictEqual(editor, self.editor_1_dict)

    def test_fetch_multiple_editors(self):
        self.editor_query.return_value = [editor_1, editor_2]
        editors = mb_editor.fetch_multiple_editors([2323, 2324])
        self.assertDictEqual(editors[2323], self.editor_1_dict)
        self.assertDictEqual(editors[2324], self.editor_2_dict)

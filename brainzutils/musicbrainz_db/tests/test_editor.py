from datetime import datetime

import pytest
from mbdata.models import Editor
from psycopg2.tz import FixedOffsetTimezone

from brainzutils.musicbrainz_db import editor as mb_editor


@pytest.mark.database
class TestEditor:
    editor_dt = datetime(2014, 12, 1, 14, 6, 42, 321443, tzinfo=FixedOffsetTimezone(offset=0, name=None))

    editor_1 = dict(id=2323, name="Editor 1", privs=0, member_since=editor_dt, email_confirm_date=editor_dt,
                    last_login_date=editor_dt, last_updated=editor_dt, deleted=False, password="{CLEARTEXT}pass",
                    ha1="3f3edade87115ce351d63f42d92a1834")
    expected_editor_1 = {
        'area': None,
        'bio': None,
        'birth_date': None,
        'deleted': False,
        'email': None,
        'email_confirm_date': editor_dt,
        'gender': None,
        'id': 2323,
        'last_login_date': editor_dt,
        'last_updated': editor_dt,
        'member_since': editor_dt,
        'name': 'Editor 1',
        'privs': 0,
        'website': None
    }

    editor_2 = dict(id=2324, name="Editor 2", privs=3, email="editor@example.com", website="example.com",
                    bio="Random\neditor", member_since=editor_dt, email_confirm_date=editor_dt,
                    last_login_date=editor_dt, last_updated=editor_dt, deleted=False, area=None,
                    password="$2b$12$2odiKUAGktuwM2J.tp/uZ.54bniapSMjCln3J1TfC6zx74QFuawQ6",
                    ha1="3f3edade87115ce351d63f42d92a1834")
    expected_editor_2 = {
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
        "birth_date": None,
        "deleted": False,
        "gender": None,
        "area": None,
    }

    def test_get_by_id(self, session):
        # Manually adding and deleting data in tests can get tedious. However, we have only two tests for which this is
        # needed. In case in future we need to add more tests where the test database needs to be modified, we should
        # explore other alternatives to ease the process.
        with session as db:
            # The editors table in test database has many empty columns and fields like last_login_date may change with
            # new dump.
            insert_editor_1 = Editor(**TestEditor.editor_1)
            db.add(insert_editor_1)
            db.commit()
            try:
                editor = mb_editor.get_editor_by_id(2323)
                assert editor == TestEditor.expected_editor_1
            finally:
                # regardless whether the assertion fails or passes, delete the inserted editor to prevent side effects
                # on subsequent tests
                db.delete(insert_editor_1)
                db.commit()

    def test_fetch_multiple_editors(self, session):
        # Manually adding and deleting data in tests can get tedious. However, we have only two tests for which this is
        # needed. In case in future we need to add more tests where the test database needs to be modified, we should
        # explore other alternatives to ease the process.
        with session as db:
            # The editors table in test database has many empty columns and fields like last_login_date may change with
            # new dump.
            insert_editor_1 = Editor(**TestEditor.editor_1)
            insert_editor_2 = Editor(**TestEditor.editor_2)
            db.add(insert_editor_1)
            db.add(insert_editor_2)
            db.commit()
            try:
                editors = mb_editor.fetch_multiple_editors([2323, 2324])
                assert editors[2323] == TestEditor.expected_editor_1
                assert editors[2324] == TestEditor.expected_editor_2
            finally:
                # regardless whether the assertion fails or passes, delete the inserted editor to prevent side effects
                # on subsequent tests
                db.delete(insert_editor_1)
                db.delete(insert_editor_2)
                db.commit()

    def test_fetch_multiple_editors_empty(self, engine):
        editors = mb_editor.fetch_multiple_editors(
            [2323, 2324],
        )
        assert editors == {}

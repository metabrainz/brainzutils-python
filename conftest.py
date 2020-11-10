import pytest

from brainzutils.musicbrainz_db import init_db_engine


@pytest.fixture(scope="session")
def engine():
    init_db_engine("postgresql://musicbrainz@musicbrainz_db/musicbrainz_db")

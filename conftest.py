import pytest

from brainzutils.musicbrainz_db import init_db_engine, mb_session


@pytest.fixture(scope="session")
def engine():
    init_db_engine("postgresql://musicbrainz@musicbrainz_db/musicbrainz_db")


@pytest.fixture(scope="function")
def session(engine):
    return mb_session()

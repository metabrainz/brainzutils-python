from brainzutils import cache
from brainzutils.musicbrainz_db import mb_session
from brainzutils.musicbrainz_db.includes import check_includes
from brainzutils.musicbrainz_db.serialize import serialize_recording
from brainzutils.musicbrainz_db.utils import get_entities_by_gids
from collections import defaultdict
from mbdata.models import Recording
from sqlalchemy.orm import joinedload, subqueryload


def get_recording_by_mbid(mbid, includes=None):
    """ Get recording with MusicBrainz ID.

    Args:
        mbid (uuid): MBID(gid) of the recording.
        includes (list): List of values to be included.
                        For list of possible values visit https://bitbucket.org/lalinsky/mbdata/wiki/API/v1/includes#!recording
    Returns:
        Dictionary containing the recording information.
    """
    if includes is None:
        includes = []
    recording = get_many_recordings_by_mbid([mbid], includes)
    return recording.get(mbid)

def get_many_recordings_by_mbid(mbids, includes=None):
    """ Get multiple recordings with MusicBrainz IDs. It fetches recordings
        using _fetch_multiple_recordings.

    Args:
        mbids (list): list of uuid (MBID(gid)) of the recordings.
        includes (list): List of values to be included.
                        For list of possible values visit https://bitbucket.org/lalinsky/mbdata/wiki/API/v1/includes#!recording
    Returns:
        Dictionary containing the recordings information with MBIDs as keys.
    """
    if includes is None:
        includes = []
    recordings = _fetch_multiple_recordings(mbids, includes)

    return recordings


def _fetch_multiple_recordings(mbids, includes=None):
    """ Fetch multiple recordings with MusicBrainz IDs.

    Args:
        mbids (list): list of uuid (MBID(gid)) of the recordings.
        includes (list): List of values to be included.
                        For list of possible values visit https://bitbucket.org/lalinsky/mbdata/wiki/API/v1/includes#!recording
    Returns:
        Dictionary containing the recordings information with MBIDs as keys.
    """
    if includes is None:
        includes = []
    includes_data = defaultdict(dict)
    check_includes('recording', includes)

    with mb_session() as db:
        query = db.query(Recording)
        
        if 'artist' in includes or 'artists' in includes:
            query = query.options(joinedload("artist_credit", innerjoin=True))

        if 'artists' in includes:
            query = query.\
            options(subqueryload("artist_credit.artists")).\
            options(joinedload("artist_credit.artists.artist", innerjoin=True))

        recordings = get_entities_by_gids(
            query=query,
            entity_type='recording',
            mbids=mbids,
        )

        recording_ids = [recording.id for recording in recordings.values()]

        if 'artist' in includes:
            for recording in recordings.values():
                includes_data[recording.id]['artist'] = recording.artist_credit

        if 'artists' in includes:
            for recording in recordings.values():
                includes_data[recording.id]['artists'] = recording.artist_credit.artists

        serial_recordings = {str(mbid): serialize_recording(recordings[mbid], includes_data[recordings[mbid].id]) for mbid in mbids}

    return serial_recordings

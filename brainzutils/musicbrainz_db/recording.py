from brainzutils import cache
from brainzutils.musicbrainz_db import mb_session, DEFAULT_CACHE_EXPIRATION
from brainzutils.musicbrainz_db.helpers import get_relationship_info
from brainzutils.musicbrainz_db.includes import check_includes
from brainzutils.musicbrainz_db.serialize import serialize_recording
from brainzutils.musicbrainz_db.utils import get_entities_by_gids
from collections import defaultdict
from mbdata.models import Recording
from sqlalchemy.orm import joinedload, subqueryload


def get_recording_by_mbid(mbid, include=[]):
    """ Get recording with MusicBrainz ID.

    Args:
        mbid (uuid): MBID(gid) of the recording.
        include (list): List of values to be included.
                        For list of possible values visit https://bitbucket.org/lalinsky/mbdata/wiki/API/v1/includes#!recording
    Returns:
        Dictionary containing the recording information.
    """

    recording = get_many_recordings_by_mbid([mbid], include)
    return recording.get(mbid)

def get_many_recordings_by_mbid(mbids, include=[]):
    """ Get multiple recordings with MusicBrainz IDs. It first checks cache for recordings and
        fetch remaining recordings using _fetch_multiple_recordings.

    Args:
        mbids (list): list of uuid (MBID(gid)) of the recordings.
        include (list): List of values to be included.
                        For list of possible values visit https://bitbucket.org/lalinsky/mbdata/wiki/API/v1/includes#!recording
    Returns:
        Dictionary containing the recordings information with MBIDs as keys.
    """

    recordings = {}
    mbids_to_fetch = []

    for mbid in mbids:
        key = cache.gen_key(mbid)
        recording = cache.get(key)
        if not recording:
            mbids_to_fetch.append(mbid)
        else:
            recordings[mbid] = recording

    recordings_fetched = _fetch_multiple_recordings(mbids_to_fetch, include)

    for mbid, recording in recordings_fetched.items():
        recordings[mbid] = recording
        cache.set(key=key, val=recording, time=DEFAULT_CACHE_EXPIRATION)
    
    return recordings


def _fetch_multiple_recordings(mbids, include=[]):
    """ Fetch multiple recordings with MusicBrainz IDs.

    Args:
        mbids (list): list of uuid (MBID(gid)) of the recordings.
        include (list): List of values to be included.
                        For list of possible values visit https://bitbucket.org/lalinsky/mbdata/wiki/API/v1/includes#!recording
    Returns:
        Dictionary containing the recordings information with MBIDs as keys.
    """

    includes_data = defaultdict(dict)
    check_includes('recording', include)

    with mb_session() as db:
        query = db.query(Recording)
        
        if 'artist' in include or 'artists' in include:
            query = query.options(joinedload("artist_credit", innerjoin=True))

        if 'artists' in include:
            query = query.\
            options(subqueryload("artist_credit.artists")).\
            options(joinedload("artist_credit.artists.artist", innerjoin=True))
        
        recordings = get_entities_by_gids(
            query=query,
            entity_type='recording',
            mbids=mbids,
        )

        recording_ids = [recording.id for recording in recordings.values()]

        if 'artist' in include:
            for recording in recordings.values():
                includes_data[recording.id]['artist'] = recording.artist_credit

        if 'artists' in include:
            for recording in recordings.values():
                includes_data[recording.id]['artists'] = recording.artist_credit.artists

        if 'url-rels' in include:
            get_relationship_info(
                db=db,
                target_type='url',
                source_type='recording',
                source_entity_ids=recording_ids,
                includes_data=includes_data,
            )

        serial_recordings = {str(mbid): serialize_recording(recordings[mbid], includes_data[recordings[mbid].id]) for mbid in mbids}

    return serial_recordings

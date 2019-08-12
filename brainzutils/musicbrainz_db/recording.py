from brainzutils.musicbrainz_db import mb_session
from brainzutils.musicbrainz_db.helpers import get_relationship_info
from brainzutils.musicbrainz_db.includes import check_includes
from brainzutils.musicbrainz_db.serialize import serialize_recording
from brainzutils.musicbrainz_db.utils import get_entities_by_gids
from collections import defaultdict
from mbdata.models import Recording
from sqlalchemy.orm import joinedload, subqueryload


def get_recording_by_mbid(mbid, includes=None, unknown_entities_for_missing=False):
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
    return fetch_multiple_recordings(
        [mbid],
        includes=includes,
        unknown_entities_for_missing=unknown_entities_for_missing,
    ).get(mbid)


def get_many_recordings_by_mbid(mbids, includes=None, unknown_entities_for_missing=False):
    """ Get multiple recordings with MusicBrainz IDs. It fetches recordings
    using fetch_multiple_recordings.

    Args:
        mbids (list): list of uuid (MBID(gid)) of the recordings.
        includes (list): List of values to be included.
                        For list of possible values visit https://bitbucket.org/lalinsky/mbdata/wiki/API/v1/includes#!recording
    Returns:
        Dictionary containing the recordings information with MBIDs as keys.
    """
    if includes is None:
        includes = []

    return fetch_multiple_recordings(
        mbids,
        includes,
        unknown_entities_for_missing=unknown_entities_for_missing,
    )


def fetch_multiple_recordings(mbids, includes=None, unknown_entities_for_missing=False):
    """ Fetch multiple recordings with MusicBrainz IDs.

    Args:
        mbids (list): list of uuid (MBID(gid)) of the recordings.
        includes (list): List of values to be included.
                        For list of possible values visit https://bitbucket.org/lalinsky/mbdata/wiki/API/v1/includes#!recording
    Returns:
        Dictionary containing the recording information with MBIDs as keys.
            - id: Recording mbid
            - name: Name of the recording
            - length: length of the recording
            - artists:
                - artist information: id, name, credited_name and join_phrase
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
            unknown_entities_for_missing=unknown_entities_for_missing,
        )

        recording_ids = [recording.id for recording in recordings.values()]

        if 'rating' in includes:
            for recording in recordings.values():
                includes_data[recording.id]['rating'] = recording.rating

        if 'artist' in includes:
            for recording in recordings.values():
                includes_data[recording.id]['artist'] = recording.artist_credit

        if 'artists' in includes:
            for recording in recordings.values():
                includes_data[recording.id]['artists'] = recording.artist_credit.artists

        if 'url-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='url',
                source_type='recording',
                source_entity_ids=recording_ids,
                includes_data=includes_data,
            )

        if 'work-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='work',
                source_type='recording',
                source_entity_ids=recording_ids,
                includes_data=includes_data,
            )

        serial_recordings = {str(mbid): serialize_recording(recordings[mbid], includes_data[recordings[mbid].id]) for mbid in mbids}

    return serial_recordings

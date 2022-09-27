from brainzutils.musicbrainz_db import mb_session
from brainzutils.musicbrainz_db.helpers import get_relationship_info
from brainzutils.musicbrainz_db.includes import check_includes
from brainzutils.musicbrainz_db.serialize import serialize_recording
from brainzutils.musicbrainz_db.utils import get_entities_by_gids
from collections import defaultdict
from mbdata.models import Recording, ArtistCredit, ArtistCreditName
from sqlalchemy.orm import joinedload, subqueryload


def get_recording_by_mbid(mbid, includes=None):
    """ Get recording with MusicBrainz ID.

    Args:
        mbid (uuid): MBID(gid) of the recording.
        includes (list): List of values to be included.
                        For list of possible values visit https://bitbucket.org/lalinsky/mbdata/wiki/API/v1/includes#!recording
    Returns:
        Dictionary containing the recording information, or None if the recording doesn't exist.
    """
    if includes is None:
        includes = []
    return fetch_multiple_recordings(
        [mbid],
        includes=includes,
    ).get(mbid)


def get_many_recordings_by_mbid(mbids, includes=None):
    """ Get multiple recordings with MusicBrainz IDs. It fetches recordings
    using fetch_multiple_recordings.

    Args:
        mbids (list): list of uuid (MBID(gid)) of the recordings.
        includes (list): List of values to be included.
                        For list of possible values visit https://bitbucket.org/lalinsky/mbdata/wiki/API/v1/includes#!recording
    Returns:
        A dictionary containing the recording's information with MBIDs as keys.
        If an MBID doesn't exist in the database, it isn't returned.
        If an MBID is a redirect, the dictionary key will be the MBID given as an argument,
         but the returned object will contain the new MBID in the 'mbid' key.
    """
    if includes is None:
        includes = []

    return fetch_multiple_recordings(
        mbids,
        includes,
    )


def fetch_multiple_recordings(mbids, includes=None):
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

        if 'artist' in includes:
            query = query.options(joinedload(Recording.artist_credit, innerjoin=True))

        if 'artists' in includes:
            query = query.options(
                joinedload(Recording.artist_credit, innerjoin=True).
                joinedload(ArtistCredit.artists).
                joinedload(ArtistCreditName.artist)
            )

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
                includes_data[recording.id]['artist-credit-phrase'] = recording.artist_credit.name

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

        serial_recordings = {str(mbid): serialize_recording(recording, includes_data[recording.id])
                             for mbid, recording in recordings.items()}

    return serial_recordings

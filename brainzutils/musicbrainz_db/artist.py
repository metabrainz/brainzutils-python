from collections import defaultdict
from sqlalchemy.orm import joinedload
from mbdata import models
from brainzutils.musicbrainz_db import mb_session
from brainzutils.musicbrainz_db.helpers import get_relationship_info
from brainzutils.musicbrainz_db.utils import get_entities_by_gids
from brainzutils.musicbrainz_db.serialize import serialize_artists
from brainzutils.musicbrainz_db.includes import check_includes


def get_artist_by_mbid(mbid, includes=None):
    """Get artist with MusicBrainz ID.
    Args:
        mbid (uuid): MBID(gid) of the artist.
        includes (list): List of values to be included.
                         For list of possible values see includes.py.
    Returns:
        Dictionary containing the artist information.
    """
    if includes is None:
        includes = []

    return get_many_artists_by_mbid([mbid], includes).get(mbid)


def get_many_artists_by_mbid(mbids, includes=None):
    """ Get multiple artists with MusicBrainz IDs. It fetches artists
    using _fetch_multiple_artists.

    Args:
        mbids (list): list of uuid (MBID(gid)) of the artists.
        includes (list): List of values to be included.
                         For list of possible values see includes.py.
    Returns:
        Dictionary containing the artists information with MBIDs as keys.
    """

    if includes is None:
        includes = []

    return _fetch_multiple_artists(
        mbids,
        includes=includes,
    )


def _fetch_multiple_artists(mbids, includes=None):
    """Get info related to multiple artists using their MusicBrainz IDs.
    Args:
        mbids (list): List of MBIDs of artists.
        includes (list): List of information to be included.
    Returns:
        Dictionary containing info of multiple artists keyed by their mbid.
    """

    if includes is None:
        includes = []
    includes_data = defaultdict(dict)
    check_includes('artist', includes)

    with mb_session() as db:
        query = db.query(models.Artist)

        if 'type' in includes:
            query = query.options(joinedload('type'))

        artists = get_entities_by_gids(
            query=query,
            entity_type='artist',
            mbids=mbids,
        )

        artist_ids = [artist.id for artist in artists.values()]

        if 'artist-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='artist',
                source_type='artist',
                source_entity_ids=artist_ids,
                includes_data=includes_data,
            )
        if 'url-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='url',
                source_type='artist',
                source_entity_ids=artist_ids,
                includes_data=includes_data,
            )

        if 'comment' in includes:
            for artist in artists.values():
                includes_data[artist.id]['comment'] = artist.comment

        if 'type' in includes:
            for artist in artists.values():
                includes_data[artist.id]['type'] = artist.type

    artists = {str(mbid): serialize_artists(artists[mbid], includes_data[artists[mbid].id]) for mbid in mbids}
    return artists

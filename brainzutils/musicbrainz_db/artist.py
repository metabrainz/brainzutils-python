from collections import defaultdict
from sqlalchemy.orm import joinedload
from mbdata import models
from brainzutils.musicbrainz_db import mb_session
from brainzutils.musicbrainz_db.helpers import get_relationship_info
from brainzutils.musicbrainz_db.utils import get_entities_by_gids
from brainzutils.musicbrainz_db.serialize import serialize_artists
from brainzutils.musicbrainz_db.includes import check_includes


def get_artist_by_id(mbid, includes=None, unknown_entities_for_missing=False):
    """Get artist with MusicBrainz ID.
    Args:
        mbid (uuid): MBID(gid) of the artist.
    Returns:
        Dictionary containing the artist information
    """
    if includes is None:
        includes = []

    return fetch_multiple_artists(
        [mbid],
        includes=includes,
        unknown_entities_for_missing=unknown_entities_for_missing,
    ).get(mbid)


def fetch_multiple_artists(mbids, includes=None, unknown_entities_for_missing=False):
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
        query = db.query(models.Artist).\
                options(joinedload("type"))
        artists = get_entities_by_gids(
            query=query,
            entity_type='artist',
            mbids=mbids,
            unknown_entities_for_missing=unknown_entities_for_missing,
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

    if 'rating' in includes:
        for artist in artists.values():
            includes_data[artist.id]['rating'] = artist.rating

    for artist in artists.values():
        includes_data[artist.id]['type'] = artist.type
    artists = {str(mbid): serialize_artists(artists[mbid], includes_data[artists[mbid].id]) for mbid in mbids}
    return artists

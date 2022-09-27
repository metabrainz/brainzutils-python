from collections import defaultdict
from mbdata import models
from sqlalchemy.orm import joinedload
from brainzutils.musicbrainz_db import mb_session
from brainzutils.musicbrainz_db.includes import check_includes
from brainzutils.musicbrainz_db.serialize import serialize_places
from brainzutils.musicbrainz_db.helpers import get_relationship_info
from brainzutils.musicbrainz_db.utils import get_entities_by_gids


def get_place_by_mbid(mbid, includes=None):
    """Get place with the MusicBrainz ID.

    Args:
        mbid (uuid): MBID(gid) of the place.
    Returns:
        Dictionary containing the place information, or None if the place doesn't exist.
    """
    if includes is None:
        includes = []

    return fetch_multiple_places(
        [mbid],
        includes=includes,
    ).get(mbid)


def fetch_multiple_places(mbids, includes=None):
    """Get info related to multiple places using their MusicBrainz IDs.

    Args:
        mbids (list): List of MBIDs of places.
        includes (list): List of information to be included.

    Returns:
        A dictionary containing info of multiple places keyed by their MBID.
        If an MBID doesn't exist in the database, it isn't returned.
        If an MBID is a redirect, the dictionary key will be the MBID given as an argument,
         but the returned object will contain the new MBID in the 'mbid' key.
    """
    if includes is None:
        includes = []
    includes_data = defaultdict(dict)
    check_includes('place', includes)
    with mb_session() as db:
        query = db.query(models.Place).\
            options(joinedload(models.Place.area)).\
            options(joinedload(models.Place.type))
        places = get_entities_by_gids(
            query=query,
            entity_type='place',
            mbids=mbids,
        )
        place_ids = [place.id for place in places.values()]

        if 'artist-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='artist',
                source_type='place',
                source_entity_ids=place_ids,
                includes_data=includes_data,
            )
        if 'place-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='place',
                source_type='place',
                source_entity_ids=place_ids,
                includes_data=includes_data,
            )
        if 'url-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='url',
                source_type='place',
                source_entity_ids=place_ids,
                includes_data=includes_data,
            )

        places = {str(mbid): serialize_places(place, includes_data[place.id]) for mbid, place in places.items()}
    return places

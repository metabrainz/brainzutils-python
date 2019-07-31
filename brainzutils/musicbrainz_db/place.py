from collections import defaultdict
from mbdata import models
from sqlalchemy.orm import joinedload
from brainzutils.musicbrainz_db import mb_session
from brainzutils.musicbrainz_db.includes import check_includes
from brainzutils.musicbrainz_db.serialize import serialize_places
from brainzutils.musicbrainz_db.helpers import get_relationship_info
from brainzutils.musicbrainz_db.utils import get_entities_by_gids


def get_place_by_id(mbid, includes=None, unknown_entities_for_missing=False):
    """Get place with the MusicBrainz ID.

    Args:
        mbid (uuid): MBID(gid) of the place.
    Returns:
        Dictionary containing the place information.
    """
    if includes is None:
        includes = []

    return fetch_multiple_places(
        [mbid],
        includes=includes,
        unknown_entities_for_missing=unknown_entities_for_missing,
    ).get(mbid)


def fetch_multiple_places(mbids, includes=None, unknown_entities_for_missing=False):
    """Get info related to multiple places using their MusicBrainz IDs.

    Args:
        mbids (list): List of MBIDs of places.
        includes (list): List of information to be included.

    Returns:
        Dictionary containing info of multiple places keyed by their mbid.
    """
    if includes is None:
        includes = []
    includes_data = defaultdict(dict)
    check_includes('place', includes)
    with mb_session() as db:
        query = db.query(models.Place).\
            options(joinedload("area")).\
            options(joinedload("type"))
        places = get_entities_by_gids(
            query=query,
            entity_type='place',
            mbids=mbids,
            unknown_entities_for_missing=unknown_entities_for_missing,
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

        for place in places.values():
            includes_data[place.id]['area'] = place.area
            includes_data[place.id]['type'] = place.type
        places = {str(mbid): serialize_places(places[mbid], includes_data[places[mbid].id]) for mbid in mbids}
    return places

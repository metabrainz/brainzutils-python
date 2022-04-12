from collections import defaultdict
from sqlalchemy.orm import joinedload
from mbdata import models
from brainzutils.musicbrainz_db import mb_session
from brainzutils.musicbrainz_db.utils import get_entities_by_gids
from brainzutils.musicbrainz_db.includes import check_includes
from brainzutils.musicbrainz_db.serialize import serialize_events
from brainzutils.musicbrainz_db.helpers import get_relationship_info


def get_event_by_mbid(mbid, includes=None):
    """Get event with the MusicBrainz ID.

    Args:
        mbid (uuid): MBID(gid) of the event.
    Returns:
        Dictionary containing the event information, or None if the event doesn't exist.
    """
    if includes is None:
        includes = []

    return fetch_multiple_events(
        [mbid],
        includes=includes,
    ).get(mbid)


def fetch_multiple_events(mbids, includes=None):
    """Get info related to multiple events using their MusicBrainz IDs.

    Args:
        mbids (list): List of MBIDs of events.
        includes (list): List of information to be included.

    Returns:
        A dictionary containing info of multiple events keyed by their MBID.
        If an MBID doesn't exist in the database, it isn't returned.
        If an MBID is a redirect, the dictionary key will be the MBID given as an argument,
         but the returned object will contain the new MBID in the 'mbid' key.
    """
    if includes is None:
        includes = []
    includes_data = defaultdict(dict)
    check_includes('event', includes)
    with mb_session() as db:
        query = db.query(models.Event).options(joinedload('type'))
        events = get_entities_by_gids(
            query=query,
            entity_type='event',
            mbids=mbids,
        )
        event_ids = [event.id for event in events.values()]

        if 'artist-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='artist',
                source_type='event',
                source_entity_ids=event_ids,
                includes_data=includes_data,
            )
        if 'place-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='place',
                source_type='event',
                source_entity_ids=event_ids,
                includes_data=includes_data,
            )
        if 'series-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='series',
                source_type='event',
                source_entity_ids=event_ids,
                includes_data=includes_data,
            )
        if 'url-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='url',
                source_type='event',
                source_entity_ids=event_ids,
                includes_data=includes_data,
            )
        if 'release-group-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='release_group',
                source_type='event',
                source_entity_ids=event_ids,
                includes_data=includes_data,
            )

        return {str(mbid): serialize_events(event, includes_data[event.id]) for mbid, event in events.items()}


def get_event_for_place(place_id, limit=None, offset=None):
    """Get all events linked to a place.

    Args:
        place_id (uuid): MBID of the place.
        limit (int): Max number of events to return.
        offset (int): Offset that can be used in conjunction with the limit.

    Returns:
        A tuple containing a dictionary containing info of multiple events keyed by their MBID, and the total number of events.
    """

    place_id = str(place_id)
    with mb_session() as db:
        event_query = db.query(models.Event.gid).\
            join(models.LinkEventPlace, models.Event.id == models.LinkEventPlace.entity0_id).\
            join(models.Place, models.LinkEventPlace.entity1_id == models.Place.id).\
            filter(models.Place.gid == place_id)
        
        count = event_query.count()
        events = event_query.limit(limit).offset(offset).all()
        event_ids = [event[0] for event in events]
    
    event = fetch_multiple_events(event_ids)
    return event, count

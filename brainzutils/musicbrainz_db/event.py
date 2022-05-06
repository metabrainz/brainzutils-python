from collections import defaultdict
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from mbdata import models
from uuid import UUID
from brainzutils.musicbrainz_db import mb_session
import brainzutils.musicbrainz_db.exceptions as mb_exceptions
from brainzutils.musicbrainz_db.utils import get_entities_by_gids
from brainzutils.musicbrainz_db.includes import check_includes
from brainzutils.musicbrainz_db.serialize import serialize_events
from brainzutils.musicbrainz_db.helpers import get_relationship_info

def get_mapped_event_types(event_types: list) -> list:
    """ Get event types mapped to their case sensitive name in musicbrainz.
    event_type table in the database.

    Args:
        event_types (list): List of event types.
    Returns:
        List of mapped event types.

    """
    event_types = [event_type.lower() for event_type in event_types]
    mapped_event_types = []
    with mb_session() as db:
        supported_types = [event_type.name for event_type in db.query(models.EventType).all()]
        event_type_mapping = {supported_type.lower(): supported_type for supported_type in supported_types}

        for event_type in event_types:
            if event_type in event_type_mapping:
                mapped_event_types.append(event_type_mapping[event_type])
            else:
                raise mb_exceptions.InvalidReleaseTypesError("Bad event_type: {etype} is not supported".format(etype = event_type))

        return mapped_event_types


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


def get_event_for_place(place_id: UUID, event_types: list = [],  includeNullType: bool = True, limit: int = None, offset: int = None) -> tuple:
    """Get all events linked to a place.

    Args:
        place_id (uuid): MBID of the place.
        event_types (list): List of types of events to be fetched.
        includeNullType (bool): Whether to include events with no type.
        limit (int): Max number of events to return.
        offset (int): Offset that can be used in conjunction with the limit.

    Returns:
        Tuple containing the list of dictionaries of events ordered by begin date
        and the total count of the events.
    """

    place_id = str(place_id)
    event_types = get_mapped_event_types(event_types)

    with mb_session() as db:
        event_query = db.query(models.Event).outerjoin(models.EventType).\
            join(models.LinkEventPlace, models.Event.id == models.LinkEventPlace.entity0_id).\
            join(models.Place, models.LinkEventPlace.entity1_id == models.Place.id).\
            filter(models.Place.gid == place_id)

        if includeNullType:
            event_query = event_query.filter(or_(models.Event.type == None, models.EventType.name.in_(event_types)))
        else:
            event_query = event_query.filter(models.EventType.name.in_(event_types))
        
        event_query = event_query.order_by(models.Event.begin_date_year.desc())
        count = event_query.count()
        events = event_query.limit(limit).offset(offset).all()

        return ([serialize_events(event) for event in events], count)

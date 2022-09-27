from collections import defaultdict
from typing import List
from uuid import UUID

from mbdata import models
from sqlalchemy import or_, nullslast
from sqlalchemy.orm import contains_eager, joinedload

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
                raise mb_exceptions.InvalidTypeError("Bad event_type: {etype} is not supported".format(etype = event_type))

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
        query = db.query(models.Event).options(joinedload(models.Event.type))
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


def get_events_for_place(place_id: UUID, event_types: List[str] = [],  include_null_type: bool = True, limit: int = None, offset: int = None) -> tuple:
    """Get all events that occurred at a place.

    Args:
        place_id: MBID of the place.
        event_types: List of types of events to be fetched. The supported event_types are
        'Concert', 'Festival', 'Convention/Expo', 'Launch event', 'Award ceremony', 'Stage performance', and 'Masterclass/Clinic'.
        include_null_type: Whether to include events with no type.
        limit: Max number of events to return.
        offset: Offset that can be used in conjunction with the limit.

    Returns:
        Tuple containing the list of dictionaries of events and the total count of the events.
        The list of dictionaries of events is ordered by event begin year, begin month, begin date
        begin time, and begin name. In case one of these is set to NULL, it will be ordered last.
    """

    place_id = str(place_id)
    event_types = get_mapped_event_types(event_types)

    with mb_session() as db:
        event_query = db.query(models.Event).outerjoin(models.EventType).\
            options(contains_eager(models.Event.type)).\
            join(models.LinkEventPlace, models.Event.id == models.LinkEventPlace.entity0_id).\
            join(models.Place, models.LinkEventPlace.entity1_id == models.Place.id).\
            filter(models.Place.gid == place_id)

        if include_null_type and event_types:
            event_query = event_query.filter(or_(models.Event.type == None, models.EventType.name.in_(event_types)))
        elif event_types:
            event_query = event_query.filter(models.EventType.name.in_(event_types))
        
        event_query = event_query.order_by(
            nullslast(models.Event.begin_date_year.desc()),
            nullslast(models.Event.begin_date_month.desc()),
            nullslast(models.Event.begin_date_day.desc()),
            nullslast(models.Event.time.desc()),
            nullslast(models.Event.name.asc())
        )
        count = event_query.count()
        events = event_query.limit(limit).offset(offset).all()

        return ([serialize_events(event) for event in events], count)

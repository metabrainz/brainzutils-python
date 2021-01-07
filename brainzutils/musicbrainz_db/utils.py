from brainzutils.musicbrainz_db.models import ENTITY_MODELS, META_MODELS, REDIRECT_MODELS
import brainzutils.musicbrainz_db.exceptions as mb_exceptions
from brainzutils.musicbrainz_db import unknown_entities


def unknown_entity_by_gid(entity_gid, entity_type):
    """Returns special unknown entities (in case, they are not present in MB).

    Args:
        entity_gid: MBID of the unknown entity.
        entity_type: Type of the unknown entity.
    Returns:
        Special entity object (unknown) of specified entity_type.
    """
    if entity_type == 'artist':
        entity = unknown_entities.unknown_artist
    if entity_type == 'release_group':
        entity = unknown_entities.unknown_release_group
    elif entity_type == 'recording':
        entity = unknown_entities.unknown_recording
    elif entity_type == 'release':
        entity = unknown_entities.unknown_release
    elif entity_type == 'artist':
        entity = unknown_entities.unknown_artist
    elif entity_type == 'place':
        entity = unknown_entities.unknown_place
    elif entity_type == 'event':
        entity = unknown_entities.unknown_event
    elif entity_type == 'label':
        entity = unknown_entities.unknown_label
    elif entity_type == 'work':
        entity = unknown_entities.unknown_work
    else:
        raise mb_exceptions.InvalidTypeError("Couldn't create unknown for invalid type: {type}".format(type=entity_type))

    entity.gid = entity_gid
    return entity


def unknown_entity_by_id(entity_id, entity_type):
    """Returns special unknown entities (in case, they are not present in MB).

    Args:
        entity_id: ID of the unknown entity.
        entity_type: Type of the unknown entity.
    Returns:
        Special entity object (unknown) of specified entity_type.
    """
    if entity_type == 'editor':
        entity = unknown_entities.unknown_editor(id=0)
    else:
        raise mb_exceptions.InvalidTypeError("Couldn't create unknown for invalid type: {type}".format(type=entity_type))

    entity.id = entity_id
    return entity


def get_entities_by_gids(query, entity_type, mbids, unknown_entities_for_missing=False):
    """Get entities using their MBIDs.

    An entity can have multiple MBIDs. This function may be passed another
    MBID of an entity, in which case, it is redirected to the original entity.

    Note that the query may be modified before passing it to this
    function in order to save queries made to the database.

    Args:
        query (Query): SQLAlchemy Query object.
        entity_type (str): Type of entity being queried.
        mbids (list): IDs of the target entities.
        unknown_entities_for_missing (bool): If set, NoDataFoundException is suppressed and unknown entities are returned instead.

    Returns:
        Dictionary of objects of target entities keyed by their MBID.
    """
    entity_model = ENTITY_MODELS[entity_type]
    results = query.filter(entity_model.gid.in_(mbids)).all()
    remaining_gids = list(set(mbids) - {entity.gid for entity in results})
    entities = {str(entity.gid): entity for entity in results}

    if entity_type in META_MODELS:
        meta_model = META_MODELS[entity_type]
        query = query.add_entity(meta_model).join(meta_model)
        entity_ids = list({entity.id for entity in results})
        results = query.filter(meta_model.id.in_(entity_ids))
        for entity, entity_meta in results:
            entities[entity.gid].rating = entity_meta.rating

    if remaining_gids:
        redirect_model = REDIRECT_MODELS[entity_type]
        query = query.add_entity(redirect_model).join(redirect_model)
        results = query.filter(redirect_model.gid.in_(remaining_gids))

        redirect_gids = set()
        if entity_type in META_MODELS:
            for entity, _, redirect_obj in results:
                entities[redirect_obj.gid] = entity
                redirect_gids.add(redirect_obj.gid)
        else:
            for entity, redirect_obj in results:
                entities[redirect_obj.gid] = entity
                redirect_gids.add(redirect_obj.gid)

        remaining_gids = list(set(remaining_gids) - redirect_gids)

    if remaining_gids:
        if unknown_entities_for_missing:
            for gid in remaining_gids:
                entities[gid] = unknown_entity_by_gid(gid, entity_type)
        else:
            raise mb_exceptions.NoDataFoundException("Couldn't find entities with IDs: {mbids}".format(mbids=remaining_gids))

    return entities


def get_entities_by_ids(query, entity_type, ids, unknown_entities_for_missing=False):
    """Get entities using their IDs.

    Note that the query may be modified before passing it to this
    function in order to save queries made to the database.

    Args:
        query (Query): SQLAlchemy Query object.
        entity_type (str): Type of entity being queried.
        ids (list): IDs of the target entities.
        unknown_entities_for_missing (bool): If set, NoDataFoundException is suppressed and unknown entities are returned instead.

    Returns:
        Dictionary of objects of target entities keyed by their ID.
    """
    entity_model = ENTITY_MODELS[entity_type]
    results = query.filter(entity_model.id.in_(ids)).all()
    remaining_ids = list(set(ids) - {entity.id for entity in results})
    entities = {entity.id: entity for entity in results}

    if remaining_ids:
        if unknown_entities_for_missing:
            for entity_id in remaining_ids:
                entities[entity_id] = unknown_entity_by_id(entity_id, entity_type)
        else:
            raise mb_exceptions.NoDataFoundException(
                "Couldn't find entities with IDs: {ids}".format(ids=remaining_ids))

    return entities

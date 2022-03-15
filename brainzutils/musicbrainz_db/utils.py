from brainzutils.musicbrainz_db.models import ENTITY_MODELS, META_MODELS, REDIRECT_MODELS
import brainzutils.musicbrainz_db.exceptions as mb_exceptions


def get_entities_by_gids(query, entity_type, mbids):
    """Get entities using their MBIDs.

    An entity can have multiple MBIDs. This function may be passed another
    MBID of an entity, in which case, it is redirected to the original entity.

    Note that the query may be modified before passing it to this
    function in order to save queries made to the database.

    Args:
        query (Query): SQLAlchemy Query object.
        entity_type (str): Type of entity being queried.
        mbids (list): IDs of the target entities.

    Returns:
        Dictionary of objects of target entities keyed by their MBID.
    """
    entity_model = ENTITY_MODELS[entity_type]
    if entity_type in META_MODELS:
        meta_model = META_MODELS[entity_type]
        query = query.add_entity(meta_model).join(meta_model)

    results = query.filter(entity_model.gid.in_(mbids)).all()
    entity_gids = set()
    entities = {}
    if entity_type in META_MODELS:
        for entity, entity_meta in results:
            entities[entity.gid] = entity
            entities[entity.gid].rating = entity_meta.rating
            entity_gids.add(entity.gid)
    else:
        entities = {str(entity.gid): entity for entity in results}
        entity_gids = {entity.gid for entity in results}

    remaining_gids = list(set(mbids) - entity_gids)
    if remaining_gids:
        redirect_model = REDIRECT_MODELS[entity_type]
        query = query.add_entity(redirect_model).join(redirect_model)
        results = query.filter(redirect_model.gid.in_(remaining_gids))

        redirect_gids = set()
        if entity_type in META_MODELS:
            for entity, entity_meta, redirect_obj in results:
                entities[redirect_obj.gid] = entity
                entities[redirect_obj.gid].rating = entity_meta.rating
                redirect_gids.add(redirect_obj.gid)
        else:
            for entity, redirect_obj in results:
                entities[redirect_obj.gid] = entity
                redirect_gids.add(redirect_obj.gid)

    return entities


def get_entities_by_ids(query, entity_type, ids):
    """Get entities using their IDs.

    Note that the query may be modified before passing it to this
    function in order to save queries made to the database.

    Args:
        query (Query): SQLAlchemy Query object.
        entity_type (str): Type of entity being queried.
        ids (list): IDs of the target entities.

    Returns:
        Dictionary of objects of target entities keyed by their ID.
    """
    entity_model = ENTITY_MODELS[entity_type]
    results = query.filter(entity_model.id.in_(ids)).all()
    entities = {entity.id: entity for entity in results}

    return entities

import brainzutils.musicbrainz_db.exceptions as mb_exceptions
from mbdata import models


# Entity models
ENTITY_MODELS = {
    'artist': models.Artist,
    'place': models.Place,
    'release_group': models.ReleaseGroup,
    'release': models.Release,
    'event': models.Event,
    'label': models.Label,
    'series': models.Series,
    'url': models.URL,
    'recording': models.Recording,
    'work': models.Work,
    'editor': models.Editor,
}


# Redirect models
REDIRECT_MODELS = {
    'place': models.PlaceGIDRedirect,
    'artist': models.ArtistGIDRedirect,
    'release': models.ReleaseGIDRedirect,
    'release_group': models.ReleaseGroupGIDRedirect,
    'event': models.EventGIDRedirect,
    'label': models.LabelGIDRedirect,
    'recording': models.RecordingGIDRedirect,
    'work': models.WorkGIDRedirect,
}


def _filter_entity_model_by_gid(query, entity_type, mbids):
    entity_model = ENTITY_MODELS[entity_type]
    results = query.filter(entity_model.gid.in_(mbids)).all()
    remaining_gids = list(set(mbids) - {entity.gid for entity in results})
    entities = {str(entity.gid): entity for entity in results}
    return entities, remaining_gids


def _filter_redirect_model_by_gid(query, entity_type, entities, remaining_gids):
    if remaining_gids:
        redirect_model = REDIRECT_MODELS[entity_type]
        query = query.add_entity(redirect_model).join(redirect_model)
        results = query.filter(redirect_model.gid.in_(remaining_gids))
        for entity, redirect_obj in results:
            entities[redirect_obj.gid] = entity
        remaining_gids = list(set(remaining_gids) - {redirect_obj.gid for entity, redirect_obj in results})
    return entities, remaining_gids


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

    Returns:d
        Dictionary of objects of target entities keyed by their MBID.
    """
    entities, remaining_gids = _filter_entity_model_by_gid(query, entity_type, mbids)
    entities, remaining_gids = _filter_redirect_model_by_gid(query, entity_type, entities, remaining_gids)

    if remaining_gids:
        raise mb_exceptions.NoDataFoundException("Couldn't find entities with IDs: {mbids}".format(mbids=remaining_gids))

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
    remaining_ids = list(set(ids) - {entity.id for entity in results})
    entities = {entity.id: entity for entity in results}

    if remaining_ids:
        raise mb_exceptions.NoDataFoundException(
            "Couldn't find entities with IDs: {ids}".format(ids=remaining_ids))

    return entities
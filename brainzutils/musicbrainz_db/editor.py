from collections import defaultdict
from sqlalchemy.orm import joinedload
from mbdata import models
from brainzutils.musicbrainz_db import mb_session
from brainzutils.musicbrainz_db.utils import get_entities_by_ids
from brainzutils.musicbrainz_db.serialize import serialize_editor
from brainzutils.musicbrainz_db.includes import check_includes


def get_editor_by_id(editor_id, includes=None):
    """Get editor with editor ID.
    Args:
        editor_id (int): ID of the editor.
    Returns:
        Dictionary containing the editor information
    """
    if includes is None:
        includes = []

    return fetch_multiple_editors(
        [editor_id],
        includes=includes,
    ).get(editor_id)


def fetch_multiple_editors(editor_ids, includes=None):
    """Get info related to multiple editors using their editor IDs.
    Args:
        editor_ids (list): List of IDs of editors.
        includes (list): List of information to be included.
    Returns:
        Dictionary containing info of multiple editors keyed by their editor_id.
    """
    if includes is None:
        includes = []

    includes_data = defaultdict(dict)
    check_includes('editor', includes)
    with mb_session() as db:
        query = db.query(models.Editor)
        editors = get_entities_by_ids(
            query=query,
            entity_type='editor',
            ids=editor_ids,
        )
        editor_ids = [editor.id for editor in editors.values()]
        editors = {editor_id: serialize_editor(editors[editor_id], includes_data) for editor_id in editor_ids}

    return editors

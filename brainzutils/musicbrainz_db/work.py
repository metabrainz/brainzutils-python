from collections import defaultdict
from mbdata import models
from sqlalchemy.orm import joinedload
from brainzutils.musicbrainz_db import mb_session
from brainzutils.musicbrainz_db.utils import get_entities_by_gids
from brainzutils.musicbrainz_db.includes import check_includes
from brainzutils.musicbrainz_db.serialize import serialize_works
from brainzutils.musicbrainz_db.helpers import get_relationship_info


def get_work_by_id(mbid, includes=None, unknown_entities_for_missing=False):
    """Get work with the MusicBrainz ID.

    Args:
        mbid (uuid): MBID(gid) of the work.
    Returns:
        Dictionary containing the work information.
    """
    if includes is None:
        includes = []

    return fetch_multiple_works(
        [mbid],
        includes=includes,
        unknown_entities_for_missing=unknown_entities_for_missing,
    ).get(mbid)


def fetch_multiple_works(mbids, includes=None, unknown_entities_for_missing=False):
    """Get info related to multiple works using their MusicBrainz IDs.

    Args:
        mbids (list): List of MBIDs of works.
        includes (list): List of information to be included.

    Returns:
        Dictionary containing info of multiple works keyed by their mbid.
    """
    if includes is None:
        includes = []
    includes_data = defaultdict(dict)
    check_includes('work', includes)
    with mb_session() as db:
        query = db.query(models.Work).\
            options(joinedload("type"))
        works = get_entities_by_gids(
            query=query,
            entity_type='work',
            mbids=mbids,
            unknown_entities_for_missing=unknown_entities_for_missing,
        )
        work_ids = [work.id for work in works.values()]

        if 'artist-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='artist',
                source_type='work',
                source_entity_ids=work_ids,
                includes_data=includes_data,
            )

        if 'recording-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='recording',
                source_type='work',
                source_entity_ids=work_ids,
                includes_data=includes_data,
            )
        for work in works.values():
            includes_data[work.id]['type'] = work.type
    return {str(mbid): serialize_works(works[mbid], includes_data[works[mbid].id]) for mbid in mbids}

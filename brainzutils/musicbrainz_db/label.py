from collections import defaultdict
from mbdata import models
from sqlalchemy.orm import joinedload
from brainzutils.musicbrainz_db import mb_session
from brainzutils.musicbrainz_db.utils import get_entities_by_gids
from brainzutils.musicbrainz_db.includes import check_includes
from brainzutils.musicbrainz_db.serialize import serialize_labels
from brainzutils.musicbrainz_db.helpers import get_relationship_info


def get_label_by_mbid(mbid, includes=None):
    """Get label with the MusicBrainz ID.

    Args:
        mbid (uuid): MBID(gid) of the label.
    Returns:
        Dictionary containing the label information, or None if the label doesn't exist.
    """
    if includes is None:
        includes = []

    return fetch_multiple_labels(
        [mbid],
        includes=includes,
    ).get(mbid)


def fetch_multiple_labels(mbids, includes=None):
    """Get info related to multiple labels using their MusicBrainz IDs.

    Args:
        mbids (list): List of MBIDs of labels.
        includes (list): List of information to be included.
    Returns:
        A dictionary containing info of multiple labels keyed by their MBID.
        If an MBID doesn't exist in the database, it isn't returned.
        If an MBID is a redirect, the dictionary key will be the MBID given as an argument,
         but the returned object will contain the new MBID in the 'mbid' key.
    """
    if includes is None:
        includes = []
    includes_data = defaultdict(dict)
    check_includes('label', includes)
    with mb_session() as db:
        query = db.query(models.Label).\
            options(joinedload(models.Label.type)).\
            options(joinedload(models.Label.area))
        labels = get_entities_by_gids(
            query=query,
            entity_type='label',
            mbids=mbids,
        )
        label_ids = [label.id for label in labels.values()]

        if 'artist-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='artist',
                source_type='label',
                source_entity_ids=label_ids,
                includes_data=includes_data,
            )

        if 'url-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='url',
                source_type='label',
                source_entity_ids=label_ids,
                includes_data=includes_data,
            )

        return {str(mbid): serialize_labels(label, includes_data[label.id]) for mbid, label in labels.items()}

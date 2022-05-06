from collections import defaultdict
from mbdata import models
from sqlalchemy import nullslast
from sqlalchemy.orm import joinedload
from brainzutils.musicbrainz_db import mb_session
from brainzutils.musicbrainz_db.includes import check_includes
from brainzutils.musicbrainz_db.serialize import serialize_release_groups
from brainzutils.musicbrainz_db.utils import get_entities_by_gids
from brainzutils.musicbrainz_db.helpers import get_relationship_info, get_tags


def get_release_group_by_mbid(mbid, includes=None):
    """Get release group with the MusicBrainz ID.
    Args:
        mbid (uuid): MBID(gid) of the release group.
    Returns:
        Dictionary containing the release group information, or None if the release group doesn't exist.
    """
    if includes is None:
        includes = []

    return fetch_multiple_release_groups(
        [mbid],
        includes=includes,
    ).get(mbid)


def fetch_multiple_release_groups(mbids, includes=None):
    """Get info related to multiple release groups using their MusicBrainz IDs.
    Args:
        mbids (list): List of MBIDs of releases groups.
        includes (list): List of information to be included.
    Returns:
        A dictionary containing info of multiple release groups keyed by their MBID.
        If an MBID doesn't exist in the database, it isn't returned.
        If an MBID is a redirect, the dictionary key will be the MBID given as an argument,
         but the returned object will contain the new MBID in the 'mbid' key.
    """
    if includes is None:
        includes = []
    includes_data = defaultdict(dict)
    check_includes('release_group', includes)
    with mb_session() as db:
        # Join table meta which contains release date for a release group
        query = db.query(models.ReleaseGroup).options(joinedload("meta")).\
                options(joinedload("type"))

        if 'artists' in includes:
            query = query.\
                options(joinedload("artist_credit")).\
                options(joinedload("artist_credit.artists")).\
                options(joinedload("artist_credit.artists.artist"))

        release_groups = get_entities_by_gids(
            query=query,
            entity_type='release_group',
            mbids=mbids,
        )
        release_group_ids = [release_group.id for release_group in release_groups.values()]

        if 'artists' in includes:
            for release_group in release_groups.values():
                artist_credit_names = release_group.artist_credit.artists
                includes_data[release_group.id]['artist-credit-names'] = artist_credit_names
                includes_data[release_group.id]['artist-credit-phrase'] = release_group.artist_credit.name

        if 'releases' in includes:
            query = db.query(models.Release).filter(getattr(models.Release, "release_group_id").in_(release_group_ids))
            for release in query:
                includes_data[release.release_group_id].setdefault('releases', []).append(release)

        if 'release-group-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='release_group',
                source_type='release_group',
                source_entity_ids=release_group_ids,
                includes_data=includes_data,
            )

        if 'url-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='url',
                source_type='release_group',
                source_entity_ids=release_group_ids,
                includes_data=includes_data,
            )

        if 'work-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='work',
                source_type='release_group',
                source_entity_ids=release_group_ids,
                includes_data=includes_data,
            )

        if 'tags' in includes:
            release_group_tags = get_tags(
                db=db,
                entity_model=models.ReleaseGroup,
                tag_model=models.ReleaseGroupTag,
                foreign_tag_id=models.ReleaseGroupTag.release_group_id,
                entity_ids=release_group_ids,
            )
            for release_group_id, tags in release_group_tags:
                includes_data[release_group_id]['tags'] = tags

        for release_group in release_groups.values():
            includes_data[release_group.id]['meta'] = release_group.meta
        release_groups = {str(mbid): serialize_release_groups(release_group, includes_data[release_group.id])
                          for mbid, release_group in release_groups.items()}
        return release_groups


def get_release_groups_for_artist(artist_id, release_types=None, limit=None, offset=None):
    """Get all release groups linked to an artist.

    Args:
        artist_id (uuid): MBID of the artist.
        release_types (list): List of types of release groups to be fetched.
        limit (int): Max number of release groups to return.
        offset (int): Offset that can be used in conjunction with the limit.

    Returns:
        Tuple containing the list of dictionaries of release groups ordered by release year
        and the total count of the release groups.
    """
    artist_id = str(artist_id)
    includes_data = defaultdict(dict)
    if release_types is None:
        release_types = []
    release_types = [release_type.lower() for release_type in release_types]
    # map release types to their case sensitive name in musicbrainz.release_group_primary_type table in the database
    release_types_mapping = {
        'album': 'Album',
        'single': 'Single',
        'ep': 'EP',
        'broadcast': 'Broadcast',
        'other': 'Other'
    }
    release_types = [release_types_mapping[release_type] for release_type in release_types]
    with mb_session() as db:
        release_groups_query = _get_release_groups_for_artist_query(db, artist_id, release_types)
        count = release_groups_query.count()
        release_groups = release_groups_query.order_by(
            nullslast(models.ReleaseGroupMeta.first_release_date_year.desc())
        ).limit(limit).offset(offset).all()

        for release_group in release_groups:
            includes_data[release_group.id]['meta'] = release_group.meta
        release_groups = ([serialize_release_groups(release_group, includes_data[release_group.id])
                            for release_group in release_groups], count)
        return release_groups


def _get_release_groups_for_artist_query(db, artist_id, release_types):
    return db.query(models.ReleaseGroup).\
        options(joinedload('meta')).\
        join(models.ReleaseGroupPrimaryType).join(models.ReleaseGroupMeta).\
        join(models.ArtistCreditName, models.ArtistCreditName.artist_credit_id == models.ReleaseGroup.artist_credit_id).\
        join(models.Artist, models.Artist.id == models.ArtistCreditName.artist_id).\
        filter(models.Artist.gid == artist_id).filter(models.ReleaseGroupPrimaryType.name.in_(release_types))


def get_release_groups_for_label(label_id, release_types=None, limit=None, offset=None):
    """Get all release groups linked to a label.

    Args:
        label_id (uuid): MBID of the label.
        release_types (list): List of types of release groups to be fetched.
        limit (int): Max number of release groups to return.
        offset (int): Offset that can be used in conjunction with the limit.

    Returns:
        Tuple containing the list of dictionaries of release groups ordered by release year
        and the total count of the release groups.
    """
    label_id = str(label_id)
    includes_data = defaultdict(dict)
    if release_types is None:
        release_types = []
    release_types = [release_type.lower() for release_type in release_types]
    # map release types to their case sensitive name in musicbrainz.release_group_primary_type table in the database
    release_types_mapping = {
        'album': 'Album',
        'single': 'Single',
        'ep': 'EP',
        'broadcast': 'Broadcast',
        'other': 'Other'
    }
    release_types = [release_types_mapping[release_type] for release_type in release_types]
    with mb_session() as db:
        release_groups_query = _get_release_groups_for_label_query(db, label_id, release_types)
        count = release_groups_query.count()
        release_groups = release_groups_query.order_by(
            nullslast(models.ReleaseGroupMeta.first_release_date_year.desc())
        ).limit(limit).offset(offset).all()

        for release_group in release_groups:
            includes_data[release_group.id]['meta'] = release_group.meta
        release_groups = [serialize_release_groups(release_group, includes_data[release_group.id])
                            for release_group in release_groups]
        return release_groups, count


def _get_release_groups_for_label_query(db, label_id, release_types):
    return db.query(models.ReleaseGroup).\
        options(joinedload('meta')).\
        join(models.ReleaseGroupPrimaryType).join(models.ReleaseGroupMeta).\
        join(models.Release, models.Release.release_group_id == models.ReleaseGroup.id).\
        join(models.ReleaseLabel, models.ReleaseLabel.release_id == models.Release.id).\
        join(models.Label, models.Label.id == models.ReleaseLabel.label_id).\
        filter(models.Label.gid == label_id).filter(models.ReleaseGroupPrimaryType.name.in_(release_types))

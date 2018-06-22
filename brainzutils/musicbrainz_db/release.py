from collections import defaultdict
from mbdata import models
from sqlalchemy.orm import joinedload
from brainzutils.musicbrainz_db import exceptions as mb_exceptions
from brainzutils.musicbrainz_db import mb_session
from brainzutils.musicbrainz_db.includes import check_includes
from brainzutils.musicbrainz_db.serialize import serialize_releases
from brainzutils.musicbrainz_db.utils import get_entities_by_gids
from brainzutils.musicbrainz_db.helpers import get_relationship_info
from brainzutils.musicbrainz_db import recording


def get_release_by_id(mbid):
    """Get release with the MusicBrainz ID.
    Args:
        mbid (uuid): MBID(gid) of the release.
    Returns:
        Dictionary containing the release information.
    """
    release = _get_release_by_id(mbid)
    return release


def _get_release_by_id(mbid):
    return fetch_multiple_releases(
        [mbid],
        includes=['media', 'release-groups'],
    ).get(mbid)


def fetch_multiple_releases(mbids, includes=None):
    """Get info related to multiple releases using their MusicBrainz IDs.
    Args:
        mbids (list): List of MBIDs of releases.
        includes (list): List of information to be included.
    Returns:
        Dictionary containing info of multiple releases keyed by their mbid.
    """
    if includes is None:
        includes = []
    includes_data = defaultdict(dict)
    check_includes('release', includes)
    with mb_session() as db:
        query = db.query(models.Release)
        if 'release-groups' in includes:
            query = query.options(joinedload('release_group'))
        if 'media' in includes:
            # Fetch media with tracks
            query = query.options(joinedload('mediums')).\
                    options(joinedload('mediums.tracks')).\
                    options(joinedload('mediums.format')).\
                    options(joinedload('mediums.tracks.recording'))
        releases = get_entities_by_gids(
            query=query,
            entity_type='release',
            mbids=mbids,
        )
        release_ids = [release.id for release in releases.values()]

        if 'release-groups' in includes:
            for release in releases.values():
                includes_data[release.id]['release-groups'] = release.release_group

        if 'media' in includes:
            for release in releases.values():
                includes_data[release.id]['media'] = release.mediums

        if 'url-rels' in includes:
            get_relationship_info(
                db=db,
                target_type='url',
                source_type='release',
                source_entity_ids=release_ids,
                includes_data=includes_data,
            )
        releases = {str(mbid): serialize_releases(releases[mbid], includes_data[releases[mbid].id]) for mbid in mbids}
    return releases


def browse_releases(release_group_id, includes=None):
    """Get all the releases by a certain release group.
    You need to provide the Release Group's MusicBrainz ID.
    """
    if includes is None:
        includes = []
    with mb_session() as db:
        release_ids = db.query(models.Release.gid).\
                      join(models.ReleaseGroup).\
                      filter(models.ReleaseGroup.gid == release_group_id).all()
        release_ids = [release_id[0] for release_id in release_ids]
    releases = fetch_multiple_releases(release_ids, includes=includes)
    return releases


def get_url_rels_from_releases(releases):
    """Returns all url-rels for a list of releases in a single list (of url-rel dictionaries)
    Typical usage with browse_releases()
    """
    all_url_rels = []
    for release_gid in releases.keys():
        if 'url-rels' in releases[release_gid]:
            all_url_rels.extend([url_rel for url_rel in releases[release_gid]['url-rels']])
    return all_url_rels


def get_releases_using_recording_mbid(recording_mbid):
    """Returns a list of releases that contain the recording with
       the given recording MBID.
    """

    # First fetch the recording so that redirects don't create any problem
    recording_redirect = recording.get_recording_by_mbid(recording_mbid)
    recording_mbid = recording_redirect['id']
    with mb_session() as db:
        releases = db.query(models.Release).\
                    join(models.Medium).\
                    join(models.Track).\
                    join(models.Recording).\
                    filter(models.Recording.gid == recording_mbid).all()

        serial_releases = [serialize_releases(release) for release in releases]
        if not serial_releases:
            raise mb_exceptions.NoDataFoundException("Couldn't find releases.")

        return serial_releases

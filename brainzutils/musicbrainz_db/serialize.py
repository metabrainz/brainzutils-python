from brainzutils.musicbrainz_db.utils import ENTITY_MODELS
from mbdata.utils.models import get_link_target
from sqlalchemy_dst import row2dict


def serialize_relationships(data, source_obj, relationship_objs):
    """Convert relationship objects to dictionaries.

    Args:
        data (dict): Dictionary containing info of source object.
        source_obj (mbdata.models): object of source entity.
        relationship_objs (dict): Dictionary containing list of objects of different relations.

    Returns:
        Dictionary containing lists of dictionaries of related entities.
    """

    for entity_type in ENTITY_MODELS:
        relation = '{0}-rels'.format(entity_type)
        if relation in relationship_objs:
            data[relation] = []
            for obj in relationship_objs[relation]:
                link_data = {
                    'type': obj.link.link_type.name,
                    'type-id': obj.link.link_type.gid,
                    'begin-year': obj.link.begin_date_year,
                    'end-year': obj.link.end_date_year,
                }
                link_data['direction'] = 'forward' if source_obj.id == obj.entity0_id else 'backward'
                if obj.link.ended:
                    link_data['ended'] = True
                link_data[entity_type] = SERIALIZE_ENTITIES[entity_type](get_link_target(obj, source_obj))
                data[relation].append(link_data)


def serialize_artist_credit(artist_credit):
    """Convert artist_credit object into a list of artist credits."""
    data = []
    for artist_credit_name in artist_credit.artists:
        artist_credit_data = {
            'id': artist_credit_name.artist.gid,
            'name': artist_credit_name.artist.name,
        }

        if artist_credit_name.name != artist_credit_name.artist.name:
            artist_credit_data['credited_name'] = artist_credit_name.name

        if artist_credit_name.join_phrase:
            artist_credit_data['join_phrase'] = artist_credit_name.join_phrase

        data.append(artist_credit_data)

    return data


def serialize_recording(recording, includes=None):
    """Convert recording objects into dictionary."""
    if includes is None:
        includes = {}
    data = {
        'id': recording.gid,
        'name': recording.name,
    }

    if recording.comment:
        data['comment'] = recording.comment

    if recording.length:
        # Divide recording length by 1000 to convert milliseconds into seconds
        data['length'] = recording.length / 1000.0

    if recording.video:
        data['video'] = True

    if 'artist' in includes:
        data['artist'] = recording.artist_credit.name
    elif 'artists' in includes:
        data['artists'] = serialize_artist_credit(recording.artist_credit)

    if 'isrc' in includes:
        data['isrcs'] = [isrc.isrc for isrc in recording.isrcs]

    return data


def serialize_artists(artist, includes=None):
    if includes is None:
        includes = {}
    data = {
        'id': artist.gid,
        'name': artist.name,
        'sort_name': artist.sort_name,
    }

    if 'type' in includes and includes['type']:
        data['type'] = includes['type'].name

    if 'relationship_objs' in includes:
        serialize_relationships(data, artist, includes['relationship_objs'])
    return data


def serialize_release_groups(release_group, includes=None):
    if includes is None:
        includes = {}

    data = {
        'id': release_group.gid,
        'title': release_group.name,
    }

    if 'type' in includes and includes['type']:
        data['type'] = includes['type'].name

    if 'artist-credit-phrase' in includes:
        data['artist-credit-phrase'] = includes['artist-credit-phrase']

    if 'meta' in includes and includes['meta'] and includes['meta'].first_release_date_year:
        data['first-release-year'] = includes['meta'].first_release_date_year

    if 'artist-credit-names' in includes:
        data['artist-credit'] = [serialize_artist_credit_names(artist_credit_name)
                                 for artist_credit_name in includes['artist-credit-names']]

    if 'releases' in includes:
        data['release-list'] = [serialize_releases(release) for release in includes['releases']]

    if 'relationship_objs' in includes:
        serialize_relationships(data, release_group, includes['relationship_objs'])

    if 'tags' in includes:
        data['tag-list'] = includes['tags']
    return data


def serialize_medium(medium, includes=None):
    if includes is None:
        includes = {}
    data = {
        'name': medium.name,
        'track_count': medium.track_count,
        'position': medium.position,
    }
    if medium.format:
        data['format'] = medium.format.name

    if 'tracks' in includes and includes['tracks']:
        data['track-list'] = [serialize_track(track) for track in includes['tracks']]
    return data


def serialize_track(track, includes=None):
    if includes is None:
        includes = {}
    data = {
        'id': track.gid,
        'name': track.name,
        'number': track.number,
        'position': track.position,
        'length': track.length,
        'recording_id': track.recording.gid,
        'recording_title': track.recording.name,
    }
    return data


def serialize_releases(release, includes=None):
    if includes is None:
        includes = {}

    data = {
        'id': release.gid,
        'name': release.name,
    }

    if 'relationship_objs' in includes:
        serialize_relationships(data, release, includes['relationship_objs'])

    if 'release-groups' in includes:
        data['release-group'] = serialize_release_groups(includes['release-groups'])

    if 'media' in includes:
        data['medium-list'] = [serialize_medium(medium, includes={'tracks': medium.tracks})
                               for medium in includes['media']]
    return data


def serialize_url(url, includes=None):
    if includes is None:
        includes = {}
    data = {
        'id': url.gid,
        'url': url.url,
    }

    if 'relationship_objs' in includes:
        serialize_relationships(data, url, includes['relationship_objs'])
    return data


def serialize_editor(editor, includes=None):
    data = row2dict(editor, exclude_pk=True, exclude={'password', 'ha1'})

    # TODO: Add includes to data here (BU-18)

    return data


SERIALIZE_ENTITIES = {
    'artist': serialize_artists,
    'release_group': serialize_release_groups,
    'release': serialize_releases,
    'medium': serialize_medium,
    'url': serialize_url,
    'editor': serialize_editor,
}

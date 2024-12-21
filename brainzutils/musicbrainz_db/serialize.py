from brainzutils.musicbrainz_db.models import ENTITY_MODELS
from mbdata.utils.models import get_link_target


def serialize_begin_end(entity):
    begin_date = entity.begin_date
    end_date = entity.end_date
    begin = []
    end = []
    if begin_date and begin_date.year:
        begin.append(f'{begin_date.year:04}')
        if begin_date.month:
            begin.append(f'{begin_date.month:02}')
            if begin_date.day:
                begin.append(f'{begin_date.day:02}')

    if end_date and end_date.year:
        end.append(f'{end_date.year:04}')
        if end_date.month:
            end.append(f'{end_date.month:02}')
            if end_date.day:
                end.append(f'{end_date.day:02}')

    data = {}
    if begin:
        data["begin"] = "-".join(begin)
    if end:
        data["end"] = "-".join(end)
    return data


def serialize_areas(area, includes=None):
    if includes is None:
        includes = {}
    data = {
        'mbid': str(area.gid),
        'name': area.name,
    }

    if area.comment:
        data['comment'] = area.comment

    dates = serialize_begin_end(area)
    if dates:
        data['life-span'] = dates

    if 'relationship_objs' in includes:
        serialize_relationships(data, area, includes['relationship_objs'])
    return data


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
                    'type-id': str(obj.link.link_type.gid),
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
            'mbid': str(artist_credit_name.artist.gid),
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
        'mbid': str(recording.gid),
        'name': recording.name,
    }

    if recording.comment:
        data['comment'] = recording.comment

    if recording.length:
        # Divide recording length by 1000 to convert milliseconds into seconds
        data['length'] = recording.length / 1000.0

    if recording.video:
        data['video'] = True

    if getattr(recording, 'rating', None):
        data['rating'] = recording.rating

    if 'artist' in includes:
        data['artist'] = recording.artist_credit.name
    elif 'artists' in includes:
        data['artists'] = serialize_artist_credit(recording.artist_credit)
        data['artist-credit-phrase'] = includes['artist-credit-phrase']

    if 'isrc' in includes:
        data['isrcs'] = [isrc.isrc for isrc in recording.isrcs]

    return data


def serialize_places(place, includes=None):
    if includes is None:
        includes = {}
    data = {
        'mbid': str(place.gid),
        'name': place.name,
        'address': place.address,
    }

    if place.comment:
        data['comment'] = place.comment

    if place.type:
        data['type'] = place.type.name

    if place.area:
        data['area'] = serialize_areas(place.area)

    if place.coordinates:
        data['coordinates'] = {
            'latitude': place.coordinates[0],
            'longitude': place.coordinates[1],
        }

    dates = serialize_begin_end(place)
    if dates:
        data['life-span'] = dates

    if 'relationship_objs' in includes:
        serialize_relationships(data, place, includes['relationship_objs'])
    return data


def serialize_labels(label, includes=None):
    if includes is None:
        includes = {}
    data = {
        'mbid': str(label.gid),
        'name': label.name,
    }

    if label.comment:
        data['comment'] = label.comment

    dates = serialize_begin_end(label)
    if dates:
        data['life-span'] = dates

    if label.type:
        data['type'] = label.type.name

    if label.area:
        data['area'] = label.area.name

    if getattr(label, 'rating', None):
        data['rating'] = label.rating

    if 'relationship_objs' in includes:
        serialize_relationships(data, label, includes['relationship_objs'])

    return data


def serialize_artists(artist, includes=None):
    if includes is None:
        includes = {}
    data = {
        'mbid': str(artist.gid),
        'name': artist.name,
        'sort_name': artist.sort_name,
    }

    if artist.comment:
        data['comment'] = artist.comment

    dates = serialize_begin_end(artist)
    if dates:
        data['life-span'] = dates

    if artist.type:
        data['type'] = artist.type.name

    if getattr(artist, 'rating', None):
        data['rating'] = artist.rating

    if 'relationship_objs' in includes:
        serialize_relationships(data, artist, includes['relationship_objs'])

    return data


def serialize_artist_credit_names(artist_credit_name):
    data = {
        'name': artist_credit_name.name,
        'artist': serialize_artists(artist_credit_name.artist),
    }
    if artist_credit_name.join_phrase:
        data['join_phrase'] = artist_credit_name.join_phrase
    return data


def serialize_release_groups(release_group, includes=None):
    if includes is None:
        includes = {}

    data = {
        'mbid': str(release_group.gid),
        'title': release_group.name,
    }

    if release_group.comment:
        data['comment'] = release_group.comment

    if release_group.type:
        data['type'] = release_group.type.name

    if getattr(release_group, 'rating', None):
        data['rating'] = release_group.rating

    if 'artist-credit-phrase' in includes:
        data['artist-credit-phrase'] = includes['artist-credit-phrase']

    if 'meta' in includes and includes['meta'].first_release_date_year:
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


def serialize_track(track):
    return {
        'mbid': str(track.gid),
        'name': track.name,
        'number': track.number,
        'position': track.position,
        'length': track.length,
        'recording_id': str(track.recording.gid),
        'recording_title': track.recording.name,
        'artist-credit': [serialize_artist_credit_names(artist_credit_name)
                          for artist_credit_name in track.recording.artist_credit.artists],
        'artist-credit-phrase': track.recording.artist_credit.name
    }


def serialize_releases(release, includes=None):
    if includes is None:
        includes = {}

    data = {
        'mbid': str(release.gid),
        'name': release.name,
    }

    if 'relationship_objs' in includes:
        serialize_relationships(data, release, includes['relationship_objs'])

    if 'release-groups' in includes:
        data['release-group'] = serialize_release_groups(includes['release-groups'])

    if 'artist-credit-phrase' in includes:
        data['artist-credit-phrase'] = includes['artist-credit-phrase']

    if 'artist-credit-names' in includes:
        data['artist-credit'] = [serialize_artist_credit_names(artist_credit_name)
                                 for artist_credit_name in includes['artist-credit-names']]

    if 'media' in includes:
        data['medium-list'] = [serialize_medium(medium, includes={'tracks': medium.tracks})
                               for medium in includes['media']]

    if release.comment:
        data['comment'] = release.comment

    return data


def serialize_events(event, includes=None):
    if includes is None:
        includes = {}
    data = {
        'mbid': str(event.gid),
        'name': event.name,
    }

    if event.comment:
        data['comment'] = event.comment

    dates = serialize_begin_end(event)
    if dates:
        data['life-span'] = dates

    if event.type:
        data['type'] = event.type.name

    if getattr(event, 'rating', None):
        data['rating'] = event.rating

    if 'relationship_objs' in includes:
        serialize_relationships(data, event, includes['relationship_objs'])
    return data


def serialize_url(url, includes=None):
    if includes is None:
        includes = {}
    data = {
        'mbid': str(url.gid),
        'url': url.url,
    }

    if 'relationship_objs' in includes:
        serialize_relationships(data, url, includes['relationship_objs'])
    return data


def serialize_works(work, includes=None):
    if includes is None:
        includes = {}
    data = {
        'mbid': str(work.gid),
        'name': work.name,
    }

    if work.comment:
        data['comment'] = work.comment

    if work.type:
        data['type'] = work.type.name

    if getattr(work, 'rating', None):
        data['rating'] = work.rating

    if 'relationship_objs' in includes:
        serialize_relationships(data, work, includes['relationship_objs'])

    return data


def serialize_editor(editor, includes=None):
    # TODO: Add includes to data here (BU-18)
    data = {
        "id": editor.id,
        "name": editor.name,
        "privs": editor.privs,
        "email": editor.email,
        "website": editor.website,
        "bio": editor.bio,
        "member_since": editor.member_since,
        "email_confirm_date": editor.email_confirm_date,
        "last_login_date": editor.last_login_date,
        "last_updated": editor.last_updated,
        "birth_date": editor.birth_date,
        "deleted": editor.deleted,
        "gender": editor.gender,
        "area": None
    }
    if editor.area:
        data["area"] = serialize_areas(editor.area)
    return data


def serialize_series(series, includes=None):
    if includes is None:
        includes = {}

    data = {
        'mbid': str(series.gid),
        'name': series.name,
    }

    if series.comment:
        data['comment'] = series.comment

    if 'relationship_objs' in includes:
        serialize_relationships(data, series, includes['relationship_objs'])

    return data


SERIALIZE_ENTITIES = {
    'artist': serialize_artists,
    'release_group': serialize_release_groups,
    'release': serialize_releases,
    'medium': serialize_medium,
    'url': serialize_url,
    'editor': serialize_editor,
    'recording': serialize_recording,
    'place': serialize_places,
    'area': serialize_areas,
    'event': serialize_events,
    'series': serialize_series,
}

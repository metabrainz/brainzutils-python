""" This module tests serialize.py """


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

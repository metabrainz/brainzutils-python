import brainzutils.musicbrainz_db.exceptions as mb_exceptions


RELATABLE_TYPES = [
    'area',
    'artist',
    'label',
    'place',
    'event',
    'recording',
    'release',
    'release-group',
    'series',
    'url',
    'work',
    'instrument'
]

RELATION_INCLUDES = [entity + '-rels' for entity in RELATABLE_TYPES]

TAG_INCLUDES = ["tags"]

VALID_INCLUDES = {
    'place': ["aliases", "annotation"] + RELATION_INCLUDES + TAG_INCLUDES,
    'event': ["aliases"] + RELATION_INCLUDES + TAG_INCLUDES,
    'recording': ["artist", "artists", "isrc"] + TAG_INCLUDES + RELATION_INCLUDES,
    'release_group': ["artists", "media", "releases"] + TAG_INCLUDES + RELATION_INCLUDES,
    'release': [
        "artists", "labels", "recordings", "release-groups", "media", "annotation", "aliases"
    ] + TAG_INCLUDES + RELATION_INCLUDES,
    'artist': ["recordings", "releases", "media", "aliases", "annotation"] + RELATION_INCLUDES + TAG_INCLUDES,
    'label': ["area", "aliases", "annotation"] + RELATION_INCLUDES + TAG_INCLUDES,
    'work': ["artists", "recordings", "aliases", "annotation"] + RELATION_INCLUDES + TAG_INCLUDES,
    'editor': [],  # TODO: List includes here (BU-18)
}


def check_includes(entity, includes):
    """Check if includes specified for an entity are valid includes."""
    for include in includes:
        if include not in VALID_INCLUDES[entity]:
            raise mb_exceptions.InvalidIncludeError("Bad includes: {inc} is not a valid include".format(inc=include))

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


# Meta models
META_MODELS = {
    'label': models.LabelMeta,
    'release_group': models.ReleaseGroupMeta,
    'event': models.EventMeta,
    'work': models.WorkMeta,
    'artist': models.ArtistMeta,
    'recording': models.RecordingMeta,
}

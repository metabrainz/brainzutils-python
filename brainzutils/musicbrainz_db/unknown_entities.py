from mbdata import models

# Unknown entities
unknown_artist = models.Artist()
unknown_artist.id = 0
unknown_artist.name = '[Unknown Artist]'
unknown_artist.sort_name = '[Unknown Artist]'

unknown_artist_credit = models.ArtistCredit()
unknown_artist_credit.id = 0
unknown_artist_credit.name = '[Unknown Artist]'

unknown_release_group = models.ReleaseGroup()
unknown_release_group.id = 0
unknown_release_group.name = '[Unknown Release Group]'

unknown_release = models.Release()
unknown_release.id = 0
unknown_release.name = '[Unknown Release]'
unknown_release.artist_credit = unknown_artist_credit

unknown_recording = models.Recording()
unknown_recording.id = 0
unknown_recording.name = '[Unknown Recording]'
unknown_recording.artist_credit = unknown_artist_credit

unknown_area = models.Area()
unknown_area.id = 0
unknown_area.name = '[Unknown Area]'

unknown_place = models.Place()
unknown_place.id = 0
unknown_place.name = '[Unknown Place]'
unknown_place.address = '[Unknown Address]'
unknown_place.area = unknown_area

unknown_event = models.Event()
unknown_event.id = 0
unknown_event.name = '[Unknown Event]'

unknown_label = models.Label()
unknown_label.id = 0
unknown_label.name = '[Unknown Label]'
unknown_label.area = unknown_area

unknown_work = models.Work()
unknown_work.id = 0
unknown_work.name = '[Unknown Work]'

unknown_editor = models.Editor
unknown_editor.name = '[Unknown Editor]'

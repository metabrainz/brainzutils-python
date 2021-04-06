from brainzutils.musicbrainz_db import place as mb_place
from brainzutils.musicbrainz_db import work as mb_work
from brainzutils.musicbrainz_db import artist as mb_artist
from brainzutils.musicbrainz_db import event as mb_event
from brainzutils.musicbrainz_db import label as mb_label
from brainzutils.musicbrainz_db import recording as mb_recording
from brainzutils.musicbrainz_db import release as mb_release

import pytest


@pytest.mark.database
class TestRedirects:

    def test_place_redirect(self, engine):
        place_redirect = mb_place.get_place_by_id("b980e2b4-c23f-4616-b2d8-7956780585dc")
        place = mb_place.get_place_by_id("36678fc4-2fee-46be-b084-4c4e2314ce71")

        place_redirect['id'] = place['id']  # except mbid, all fields should be equal. so make, mbid equal beforehand
        assert place_redirect == place

    def test_work_redirect(self, engine):
        work_redirect = mb_work.get_work_by_id("5c254ca1-0a9b-346e-a514-56e45bcad054")
        work = mb_work.get_work_by_id("59403a9a-ec62-3104-a928-73b0c18b8a04")

        work_redirect['id'] = work['id']  # except mbid, all fields should be equal. so make, mbid equal beforehand
        assert work_redirect == work

    def test_artist_redirect(self, engine):
        artist_redirect = mb_artist.get_artist_by_id("ae66081d-ef3e-4d47-b156-7cbf1f7a7cdf")
        artist = mb_artist.get_artist_by_id("5610302e-bfd9-421c-80e2-03d790a0f5e5")

        artist_redirect['id'] = artist['id']  # except mbid, all fields should be equal. so make, mbid equal beforehand
        assert artist_redirect == artist

    def test_event_redirect(self, engine):
        event_redirect = mb_event.get_event_by_id("4b039f29-1e4f-4b7e-b505-b19235023888")
        event = mb_event.get_event_by_id("8b7e7e14-0dbd-49e0-8f43-c12e7e0ea9e5")

        event_redirect['id'] = event['id']  # except mbid, all fields should be equal. so make, mbid equal beforehand
        assert event_redirect == event

    def test_label_redirect(self, engine):
        label_redirect = mb_label.get_label_by_id("d5e1e891-c17a-4fb7-980c-387a9223fe26")
        label = mb_label.get_label_by_id("c595c289-47ce-4fba-b999-b87503e8cb71")

        label_redirect['id'] = label['id']  # except mbid, all fields should be equal. so make, mbid equal beforehand
        assert label_redirect == label

    def test_recording_redirect(self, engine):
        recording_redirect = mb_recording.get_recording_by_mbid("8f1440ba-3971-4bbf-a94a-28439230ff90")
        recording = mb_recording.get_recording_by_mbid("4dd09b84-f779-4f9b-94d1-e3253aa6f040")

        recording_redirect['id'] = recording['id']  # except mbid, all fields should be equal. so make, mbid equal beforehand
        assert recording_redirect == recording

    def test_release_redirect(self, engine):
        release_redirect = mb_release.get_release_by_id("4cd143b7-fc06-35df-b2c1-c34044cba051")
        release = mb_release.get_release_by_id("dceb6a01-3431-36af-b2e1-6462193bd67c")

        release_redirect['id'] = release['id']  # except mbid, all fields should be equal. so make, mbid equal beforehand
        assert release_redirect == release

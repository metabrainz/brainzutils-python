# -*- coding: utf-8 -*-

import pytest

from brainzutils.musicbrainz_db import release_group as mb_release_group
from brainzutils.musicbrainz_db.unknown_entities import unknown_release_group


@pytest.mark.database
class TestReleaseGroup:

    def test_get_by_id(self, engine):
        release_group = mb_release_group.get_release_group_by_id(
            '0f18ec88-aa87-38a9-8a65-f03d81763560',
            includes=['artists', 'releases', 'release-group-rels', 'url-rels', 'tags']
        )

        assert release_group['id'] == '0f18ec88-aa87-38a9-8a65-f03d81763560'
        assert release_group['title'] == 'Led Zeppelin'
        # Check if multiple artists are properly fetched
        assert release_group['artist-credit-phrase'] == 'Led Zeppelin'
        assert release_group['artist-credit'][0] == {
            'name': 'Led Zeppelin',
            'artist': {
                'id': '678d88b2-87b0-403b-b63d-5da7465aecc3',
                'name': 'Led Zeppelin',
                'sort_name': 'Led Zeppelin'
            }
        }

    def test_fetch_release_groups(self, engine):
        release_groups = mb_release_group.fetch_multiple_release_groups(
            mbids=['0f18ec88-aa87-38a9-8a65-f03d81763560', '1b36a363-eec6-35ba-b0ed-34a1f2f2cd82'],
        )
        assert len(release_groups) == 2
        assert release_groups['0f18ec88-aa87-38a9-8a65-f03d81763560']['title'] == 'Led Zeppelin'
        assert release_groups['1b36a363-eec6-35ba-b0ed-34a1f2f2cd82']['title'] == 'Cosmic Thing'

    def test_fetch_release_groups_empty(self, engine):
        release_groups = mb_release_group.fetch_multiple_release_groups(
            mbids=['8ef859e3-feb2-4dd1-93da-22b91280d768', '7c1014eb-454c-3867-8854-3c95d265f8de'],
            includes=['artists', 'releases', 'release-group-rels', 'url-rels', 'work-rels', 'tags'],
            unknown_entities_for_missing=True
        )
        assert release_groups['7c1014eb-454c-3867-8854-3c95d265f8de']['title'] == unknown_release_group.name
        assert release_groups['8ef859e3-feb2-4dd1-93da-22b91280d768']['title'] == unknown_release_group.name

    def test_fetch_get_release_groups_for_artist(self, engine):
        release_groups = mb_release_group.get_release_groups_for_artist(
            artist_id='f59c5520-5f46-4d2c-b2c4-822eabf53419',
            release_types=['Single', 'EP'],
        )
        assert release_groups[0] == [{
            'id': '277ddbc8-d6fa-47fa-b652-dce7a325202f',
            'title': 'A Thousand Suns: Puerta de Alcalá',
            'first-release-year': 2010
        }]
        assert release_groups[1] == 1

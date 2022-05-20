import pytest

from brainzutils.musicbrainz_db import release_group as mb_release_group


@pytest.mark.database
class TestReleaseGroup:

    def test_get_release_group_by_mbid(self, engine):
        release_group = mb_release_group.get_release_group_by_mbid('0f18ec88-aa87-38a9-8a65-f03d81763560',
                                                                   includes=['artists', 'releases',
                                                                             'release-group-rels', 'url-rels', 'tags'])

        assert release_group['mbid'] == '0f18ec88-aa87-38a9-8a65-f03d81763560'
        assert release_group['title'] == 'Led Zeppelin'
        # Check if multiple artists are properly fetched
        assert release_group['artist-credit-phrase'] == 'Led Zeppelin'
        assert release_group['artist-credit'][0] == {
            'name': 'Led Zeppelin',
            'artist': {
                'mbid': '678d88b2-87b0-403b-b63d-5da7465aecc3',
                'name': 'Led Zeppelin',
                'sort_name': 'Led Zeppelin',
                'life-span': {'begin': '1968', 'end': '1980-09-25'},
                'type': 'Group',
            }
        }

    def test_get_release_group_by_mbid_redirect(self, engine):
        release_group = mb_release_group.get_release_group_by_mbid('358bbed4-1717-3e1c-ba8e-af54d2d3a5d6')
        assert release_group == {
            'mbid': '8a01217e-6947-3927-a39b-6691104694f1',
            'title': 'The College Dropout',
            'first-release-year': 2003,
            'type': 'Album',
            'rating': 88,
        }

    def test_fetch_release_groups(self, engine):
        release_groups = mb_release_group.fetch_multiple_release_groups(
            mbids=['0f18ec88-aa87-38a9-8a65-f03d81763560', '1b36a363-eec6-35ba-b0ed-34a1f2f2cd82'],
        )
        assert len(release_groups) == 2
        assert release_groups['0f18ec88-aa87-38a9-8a65-f03d81763560']['title'] == 'Led Zeppelin'
        assert release_groups['1b36a363-eec6-35ba-b0ed-34a1f2f2cd82']['title'] == 'Cosmic Thing'

    def test_fetch_release_groups_redirect(self, engine):
        release_groups = mb_release_group.fetch_multiple_release_groups(
            mbids=['358bbed4-1717-3e1c-ba8e-af54d2d3a5d6'],
        )
        assert release_groups == {
            '358bbed4-1717-3e1c-ba8e-af54d2d3a5d6': {
                'mbid': '8a01217e-6947-3927-a39b-6691104694f1',
                'title': 'The College Dropout',
                'first-release-year': 2003,
                'type': 'Album',
                'rating': 88,
            }
        }

    def test_fetch_release_groups_missing(self, engine):
        release_groups = mb_release_group.fetch_multiple_release_groups(
            mbids=['358bbed4-1717-3e1c-ba8e-af54d2d3a5d6', '358bbed4-1111-1111-1111-af54d2d3a5d6'],
        )
        assert list(release_groups.keys()) == ['358bbed4-1717-3e1c-ba8e-af54d2d3a5d6']

    def test_fetch_get_release_groups_for_artist(self, engine):
        release_groups = mb_release_group.get_release_groups_for_artist(
            artist_id='074e3847-f67f-49f9-81f1-8c8cea147e8e',
            release_types=['Single', 'EP'],
        )
        assert release_groups[0] == [
            {
                'mbid': '07f5e633-8846-3fe7-8e68-472b54dba159',
                'title': 'This Is What the Edge of Your Seat Was Made For',
                'first-release-year': 2004,
                'type': 'EP',
            }
        ]
        assert release_groups[1] == 1

    def test_fetch_get_release_groups_for_label(self, engine):
        release_groups = mb_release_group.get_release_groups_for_label(
            label_mbid='4cccc72a-0bd0-433a-905e-dad87871397d',
            release_types=['Album'],
        )
        assert release_groups[0][0] == {
            'mbid': 'a96597aa-93b4-4e14-9e6e-03892ab24979',
            'title': 'Watch the Throne',
            'first-release-year': 2011,
            'type': 'Album',
        }

        assert release_groups[1] == 19
        assert len(release_groups[0]) == 19

        # Test release group with null type
        release_groups_1 = mb_release_group.get_release_groups_for_label(
            label_mbid='d835e36a-78ee-48ba-ac04-b46fb37df41f',
            release_types=['Other'],
        )
        assert release_groups_1[0][0] == {
            'mbid': '39d08e6e-b877-4c64-aef9-ce79a19f6075',
            'title': 'American Songbook: The American Music Collection, Vol. III',
            'first-release-year': 1996,
        }

        assert release_groups_1[1] == 2

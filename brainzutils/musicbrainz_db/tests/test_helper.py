from collections import defaultdict

import pytest
from mbdata import models

from brainzutils.musicbrainz_db.serialize import serialize_relationships
from brainzutils.musicbrainz_db.helpers import get_relationship_info
import brainzutils.musicbrainz_db as mb
from brainzutils.musicbrainz_db.helpers import get_tags
from brainzutils.musicbrainz_db.utils import get_entities_by_gids


@pytest.mark.database
class TestHelpers:

    def test_get_tags(self, engine):
        data = defaultdict(dict)
        with mb.mb_session() as db:
            release_group_tags = get_tags(
                db=db,
                entity_model=models.ReleaseGroup,
                tag_model=models.ReleaseGroupTag,
                foreign_tag_id=models.ReleaseGroupTag.release_group_id,
                entity_ids=[253487],
            )
            for release_group_id, tags in release_group_tags:
                data[release_group_id]['tags'] = tags
            expected_data = {
                253487: {
                    'tags': ['classical', 'ballet']
                }
            }
            assert dict(data) == expected_data

    def test_get_relationship_info(self, engine):
        data = {}
        includes_data = defaultdict(dict)
        with mb.mb_session() as db:
            gid = "3185e028-9a08-448b-83e3-873dfda40476"
            place = get_entities_by_gids(
                query=db.query(models.Place),
                entity_type='place',
                mbids=[gid],
            )[gid]
            get_relationship_info(
                db=db,
                target_type='url',
                source_type='place',
                source_entity_ids=[place.id],
                includes_data=includes_data,
            )
            serialize_relationships(data, place, includes_data[place.id]['relationship_objs'])
            expected_data = {
                'url-rels': [
                    {
                        'type': 'wikidata',
                        'type-id': 'e6826618-b410-4b8d-b3b5-52e29eac5e1f',
                        'begin-year': None,
                        'end-year': None,
                        'direction': 'forward',
                        'url': {
                            'mbid': '86d64bb6-bcee-4cda-b1f8-050394664671',
                            'url': 'https://www.wikidata.org/wiki/Q2489904'
                        }
                    },
                    {
                        'type': 'discogs',
                        'type-id': '1c140ac8-8dc2-449e-92cb-52c90d525640',
                        'begin-year': None,
                        'end-year': None,
                        'direction': 'forward',
                        'url': {
                            'mbid': '06332787-5aac-4e4c-95b9-75cf729ae308',
                            'url': 'https://www.discogs.com/label/266610'
                        }
                    }
                ]
            }
            assert data == expected_data

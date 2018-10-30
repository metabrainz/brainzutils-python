===================
Database functions
===================


- *function name* = **get_artist_by_id**:
   Get artist with MusicBrainz ID.

   *Args*: mbid (uuid): 
        MBID(gid) of the artist.

   *Returns*: Dictionary containing the artist information

- *function name* = **fetch_multiple_artists**:
   Get info related to multiple artists using their MusicBrainz IDs.

   *Args*:
        mbids (list): List of MBIDs of artists.

        includes (list): List of information to be included.

   *Returns*: Dictionary containing info of multiple artists keyed by their mbid.

- *function name* = **get_editor_by_id**:
   Get editor with editor ID.

   *Args* : editor_id (int): ID of the editor.

   *Returns*: Dictionary containing the editor information

- *function name* = **fetch_multiple_editors**:
   Get info related to multiple editors using their editor IDs.

   *Args*:
        editor_ids (list): List of IDs of editors.
        includes (list): List of information to be included.

   *Returns*: Dictionary containing info of multiple editors keyed by their editor_id.

- *function name* = **get_relationship_info**:

   Get information related to relationships between different entities.

   Keep in mind that includes_data (dict) is altered to contain the relationship objects keyed by the source entity MBIDs.

   *Args*:
        db (Session object): Session object.
        target_type (str): Type of target entity.
        source_type (str): Type of source entity.
        source_entity_ids (list): IDs of the source entity.
        includes_data (dict): Dictionary containing includes data of entities.

- *function name* = **_relationship_link_helper**:
   Get relationship links between two entities.

   Keep in mind that includes_data (dict) is altered to contain the relationship objects keyed by the source entity MBIDs.

   *Args*:
        relation (mbdata.model): Model relating the two entities.
        query (Session.query): Query object.
        source_attr (str): 'entity0' or 'entity1' based on which represents source model in relation table.
        target_attr (str): 'entity0' or 'entity1' based on which represents target model in relation table.
        target_type (str): Type of the target entity.
        source_entity_ids (list): IDs of the source entity.
        includes_data (dict): Dictionary containing the includes data of entities.

- *function name* = **check_includes**:
   Check if includes specified for an entity are valid includes.

- *function name* = **get_recording_by_mbid**:

   Get recording with MusicBrainz ID.

   *Args*:
        mbid (uuid): MBID(gid) of the recording.

        includes (list): List of values to be included.
                        For list of possible values visit https://bitbucket.org/lalinsky/mbdata/wiki/API/v1/includes#!recording

   *Returns*: Dictionary containing the recording information.

- *function name* = **get_many_recordings_by_mbid**:

   Get multiple recordings with MusicBrainz IDs. It fetches recordings using fetch_multiple_recordings.

   *Args*:
        mbids (list): list of uuid (MBID(gid)) of the recordings.

        includes (list): List of values to be included.
                        For list of possible values visit https://bitbucket.org/lalinsky/mbdata/wiki/API/v1/includes#!recording

   *Returns*: Dictionary containing the recordings information with MBIDs as keys.

- *function name* = **_fetch_multiple_recordings**:

   Fetch multiple recordings with MusicBrainz IDs.

   *Args*:
        mbids (list): list of uuid (MBID(gid)) of the recordings.

        includes (list): List of values to be included.
                        For list of possible values visit https://bitbucket.org/lalinsky/mbdata/wiki/API/v1/includes#!recording

   *Returns*:
        Dictionary containing the recording information with MBIDs as keys.
            - id: Recording mbid
            - name: Name of the recording
            - length: length of the recording
            - artists:
                - artist information: id, name, credited_name and join_phrase

- *function name* = **get_release_by_id**:

   Get release with the MusicBrainz ID.

   *Args*:
        mbid (uuid): MBID(gid) of the release.

   *Returns*: Dictionary containing the release information.

- *function name* = **fetch_multiple_releases**:

   Get info related to multiple releases using their MusicBrainz IDs.

   *Args*:
        mbids (list): List of MBIDs of releases.

        includes (list): List of information to be included.

   *Returns*: Dictionary containing info of multiple releases keyed by their mbid.

- *function name* = **browse_releases**:
   Get all the releases by a certain release group.

   You need to provide the Release Group's MusicBrainz ID.

- *function name* = **get_url_rels_from_releases**:
   Returns all url-rels for a list of releases in a single list (of url-rel dictionaries)

   Typical usage with browse_releases()

- *function name* = **get_releases_using_recording_mbid**:
   Returns a list of releases that contain the recording with the given recording MBID.

   *Args*: recording_mbid (UUID): recording MBID for which releases are to be fetched.

   *Returns*:
           serial_releases (list): list with dictionary elements of following format:
            {
               'id': <release MBID>,

               'name': <release Title>,

            }

- *function name* = **serialize_relationships**:
   Convert relationship objects to dictionaries.

   *Args*:
        data (dict): Dictionary containing info of source object.
        source_obj (mbdata.models): object of source entity.
        relationship_objs (dict): Dictionary containing list of objects of different relations.

   *Returns*: Dictionary containing lists of dictionaries of related entities.

- *function name* = **serialize_artist_credit**
   Convert artist_credit object into a list of artist credits.

- *function name* = **serialize_recording**
   Convert recording objects into dictionary.

- *function name* = **get_entities_by_gids**:
   Get entities using their MBIDs.
    An entity can have multiple MBIDs. This function may be passed another
    MBID of an entity, in which case, it is redirected to the original entity.
    Note that the query may be modified before passing it to this
    function in order to save queries made to the database.

   *Args*:
        query (Query): SQLAlchemy Query object.
        entity_type (str): Type of entity being queried.
        mbids (list): IDs of the target entities.

   *Returns*:
        Dictionary of objects of target entities keyed by their MBID.

- *function name* = **get_entities_by_ids**:
   Get entities using their IDs.
    Note that the query may be modified before passing it to this
    function in order to save queries made to the database.

   *Args*:
        query (Query): SQLAlchemy Query object.
        entity_type (str): Type of entity being queried.
        ids (list): IDs of the target entities.

   *Returns*: Dictionary of objects of target entities keyed by their ID.
   
       


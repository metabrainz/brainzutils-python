FROM metabrainz/musicbrainz-test-database:beta

RUN apt-get update && apt-get install -y wget

RUN mkdir /home/musicbrainz/musicbrainz-server/setup_db
COPY scripts/* /home/musicbrainz/musicbrainz-server/setup_db/
RUN chmod +x /home/musicbrainz/musicbrainz-server/setup_db/*

RUN mkdir -p /media/dbdump
RUN chown postgres /media/dbdump

RUN rm -f /docker-entrypoint-initdb.d/create_test_db.sh
RUN ln -s /home/musicbrainz/musicbrainz-server/setup_db/create_test_db.sh /docker-entrypoint-initdb.d/
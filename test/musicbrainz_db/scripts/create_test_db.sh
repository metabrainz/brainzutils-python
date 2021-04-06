#!/usr/bin/env bash

# During the entrypoint stage, postgres is only listening on a socket
# force it to listen on localhost in order to perform the data load
pg_ctl -o "-c listen_addresses='localhost'" -w restart

cd /home/musicbrainz/musicbrainz-server
carton exec -- ./setup_db/createdb.sh -sample -fetch

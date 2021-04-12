# Musicbrainz sample database for testing

This is a postgres docker image that contains a copy of the musicbrainz database, useful
for testing.

It's based on the https://hub.docker.com/r/metabrainz/musicbrainz-test-database image, but includes
some extra scripts from [musicbrainz-docker](https://github.com/metabrainz/musicbrainz-docker) in order
to download and set up a sample database. The musicbrainz sample database is a very small subset of the
musicbrainz database, but contains real data. This makes it useful for testing on on the database
without importing everything.

This image can be run in a `docker-compose.yml` file like this:

```yaml
  musicbrainz_db:
    build:
      context: musicbrainz_db
      dockerfile: Dockerfile
    environment:
      PGDATA: /var/lib/postgresql/data/pgdata
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - "5430:5432"
```

however, this will cause the sample database to be downloaded and installed every time the container
starts up. This takes between 5-10 minutes depending on how slow your computer is.

### Image with built-in data
We also build an image and import the data musicbrainz database in order to have a container that
can start up immediately with all data imported.

This image is hosted at https://hub.docker.com/r/metabrainz/brainzutils-mb-sample-database

The steps to create a new version are manual, but should only need to be done each time
the musicbrainz schema changes.

Build the image:

    docker build -t musicbrainz_db_sample .

Start the container running bash, this is so that we can do the import and perform some cleanups.
We choose a different PGDATA location because `/var/lib/postgresql/data` by default is configured as
a volume but we don't want the data to be put in a temporary location.

    docker run -ti --rm --name musicbrainz_db_sample -e PGDATA=/var/lib/postgresql-musicbrainz/data -e POSTGRES_HOST_AUTH_METHOD=trust musicbrainz_db_sample bash

Inside the running container, run these commands

    # Start up postgres, running the entrypoint which imports the database
    /docker-entrypoint.sh postgres
    # Once the import finishes and postgres starts up, quit it with ^C
    # Remove some intermediate data and our custom entrypoint
    rm -r /media/dbdump
    rm /docker-entrypoint-initdb.d/create_test_db.sh
    grep DB_SCHEMA_SEQUENCE /home/musicbrainz/musicbrainz-server/lib/DBDefs.pm

Without quitting the container, in another terminal on the host, make a new docker commit to build 
the new image

    docker commit --change='CMD ["postgres"]' musicbrainz_db_sample metabrainz/brainzutils-mb-sample-database:schema-25-2021-04-04.0

The first argument is the container name (set with `--name` in `docker run`) and the second argument
is the name of the image to create. We include the database schema number from the grep command.

Once built, this image can be pushed to docker hub by an approved user

    docker push metabrainz/brainzutils-mb-sample-database:schema-25-2021-04-04.0

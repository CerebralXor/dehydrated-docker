# dehydrated-docker
A docker image and compose file to run [dehydrated](https://dehydrated.io) and [dns-lexicon](https://github.com/AnalogJ/lexicon) for Let's Encrypt wildcard certificates using [DNS-01](https://letsencrypt.org/docs/challenge-types/#dns-01-challenge) certificate issue and renewal, with optional [Pushover notification](https://pushover.net) upon renewal. Certificates are renewed 30 days before expiry.

## Usage:

Before first use, you need to accept the Let's Encrypt terms by running a single command. This only needs to be done once. A volume for persistent storage is required at `/dehydrated_data` to store the registration information (see https://letsencrypt.org for the terms):

`docker run -v dehydrated_data:/dehydrated_data ghcr.io/cerebralxor/dehydrated-docker:main dehydrated --register --accept-terms`

After registering and accepting the terms, the certificates can be generated and automaticlly renewed by starting the container. A mount to `/certificates` (where the generated certificates will be located), and the use of a volume at `/dehydrated_data` for persistent data is required.

`docker run -v /some/path/to/certificates:/certificates -v dehydrated_data:/dehydrated_data --env DOMAIN='domain.com *.domain.com' --env PROVIDER=namecheap --env LEXICON_NAMECHEAP_TOKEN=<TOKEN> --env LEXICON_NAMECHEAP_USERNAME=<USERNAME> ghcr.io/cerebralxor/dehydrated-docker:main`

An example [compose file](./docker-compose.yml) is also provided showing use of docker secrets to provide the credentials.

When the certificates are renewed, the date and time is written to the file `renewed` in the `certificates` mount point. This file can be monitored (for example with a [systemd PATH unit](https://www.freedesktop.org/software/systemd/man/systemd.path.html#) or inotify) to perform an action on the host when the certificates are renewed. TODO: If `/var/run/docker.sock` exists, update a specified secret and/or restart some services/containers.

### Environment variables:
_Note: All environment variables (except `LOG_LEVEL`) can be substituted with a the same name appended with `_FILE` to point to a file containing the required value instead._

The following environment variables are required:

- `DOMAIN` - A wildcard domain in this format: `domain.com *.domain.com`. See the [dehydrated documentation](https://github.com/dehydrated-io/dehydrated/blob/master/docs/domains_txt.md#wildcards) for information about the required format.
- `PROVIDER` - The DNS provider to use with lexicon. See https://dns-lexicon.readthedocs.io/en/latest/configuration_reference.html#providers-options
- The necessary API credentials for your DNS registrar that will be used by Lexicon. See https://dns-lexicon.readthedocs.io/en/latest/configuration_reference.html#passing-provider-options-to-lexicon (e.g. `LEXICON_NAMECHEAP_TOKEN` and `LEXICON_NAMECHEAP_USERNAME`)


#### Optional:

- `TZ` - Your local timezone. See https://en.wikipedia.org/wiki/List_of_tz_database_time_zones for a list of available timezones.
- `INTERVAL` - Time (in minutes) to wait before checking again for new certificates. Set to `0` to check only once and exit. Default is 720 (12 hours).
- `LOG_LEVEL` - Python log level. Either `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL`. Default is `INFO`.
- `PROVIDER_UPDATE_DELAY` - Time in seconds to wait between updating DNS records and allowing Let's Encrypt to read those records. Default is 30 seconds.
- `PUSHOVER_TOKEN` and `PUSHOVER_USER` - API credentials for [Pushover](https://pushover.net) notifications when certificates are renewed.
- `KEY_SECRET`, `CERT_SECRET`, `CHAIN_SECRET` and `FULLCHAIN_SECRET` - The prefix of docker swarm secret names that contain the respective certificate contents. If any of these environment variables are set, and `/var/run/docker.sock` is mounted, then new secrets are generated with the contents of the new certificates whenever they're updated. Note that the values only represent the prefix of the secret names. The actual secret names are constructed along with the domain name: `<PREFIX>_<DOMAINNAME>`. e.g. Using `ssl_priv_key_secret` for `KEY_SECRET` and `www.example.com` for `DOMAIN` will update the secret named `ssl_priv_key_secret_www.example.com`. Each time a certificate is renewed, a NEW secret is created with the format `<PREFIX>_<DOMAINNAME>_<TIMESTAMP>` (e.g. `2020-03-20T14.30.43`) and any services using the old secret will be updated to use the new secret. The original un-timestamped secret will also be always be updated to the latest certificates, so it can be referenced statically in a docker-compose file. The previous (now unused) timestamped secret will be removed.

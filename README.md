# dehydrated-docker
A docker image and compose file to run [dehydrated](https://dehydrated.io) and [dns-lexicon](https://github.com/AnalogJ/lexicon) for Let's Encrypt wildcard certificates using [DNS-01](https://letsencrypt.org/docs/challenge-types/#dns-01-challenge) certificate issue and renewal, with optional [Pushover notification](https://pushover.net) upon renewal.

## Usage:

First accept the terms. This only needs to be done once. A volume for persistent storage is required at `/dehydrated_data` to store the registration information (see https://letsencrypt.org for the terms):

`docker run -v dehydrated_data:/dehydrated_data ghcr.io/cerebralxor/dehydrated-docker:master dehydrated --register --accept-terms`

After registering and accepting the terms, the certificates can be generated simply by starting the container. A mount to `/certificates` (where the generated certificates will be located), and the use of a volume at `/dehydrated_data` for persistent data is required.

`docker run -v /some/path/to/certificates:/certificates -v dehydrated_data:/dehydrated_data --env DOMAIN='domain.com *.domain.com' --env PROVIDER=namecheap --env LEXICON_NAMECHEAP_TOKEN=<TOKEN> --env LEXICON_NAMECHEAP_USERNAME=<USERNAME> ghcr.io/cerebralxor/dehydrated-docker:master`

An example [compose file](./docker-compose.yml) is also provided showing use of docker secrets to provide the credentials.

When the certificates are renewed, the date and time is written to the file `renewed` in the `certificates` mount point. This file can be monitored (for example with a [systemd PATH unit](https://www.freedesktop.org/software/systemd/man/systemd.path.html#) or inotify) to perform an action on the host when the certificates are renewed.

### Environment variables:
_Note: All environment variables can be substitued with a the same name appended with `_FILE` to point to a file containing the required value instead._

The following environment variables are required:

- `DOMAIN` - A wildcard domain in this format: `domain.com *.domain.com`. See the [dehydrated documentation](https://github.com/dehydrated-io/dehydrated/blob/master/docs/domains_txt.md#wildcards) for information about the required format.
- `PROVIDER` - The DNS provider to use with lexicon. See https://dns-lexicon.readthedocs.io/en/latest/configuration_reference.html#providers-options
- The necessary API credentials for your DNS registrar that will be used by Lexicon. See https://dns-lexicon.readthedocs.io/en/latest/configuration_reference.html#passing-provider-options-to-lexicon (e.g. `LEXICON_NAMECHEAP_TOKEN` and `LEXICON_NAMECHEAP_USERNAME`)


#### Optional:

- `PROVIDER_UPDATE_DELAY` - Time in seconds to wait between updating DNS records andallowing Let's Encrypt to read those records. Default is 30 seconds.
- `PUSHOVER_TOKEN` and `PUSHOVER_USER` - API credentials for [Pushover](https://pushover.net) to send a notification when certificates are renewed.

#!/usr/bin/env python3

import datetime
import logging
import os
import sys

import docker

client = docker.from_env()

DOMAIN =        sys.argv[1]
KEYFILE =       sys.argv[2]
CERTFILE =      sys.argv[3]
FULLCHAINFILE = sys.argv[4]
CHAINFILE =     sys.argv[5]
TIMESTAMP =     datetime.datetime.now().isoformat(timespec='seconds').replace(':', '.')  # Secret names must only contain [a-zA-Z0-9-_.]

ch = logging.StreamHandler()
ch.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
ch.setFormatter(logging.Formatter('%(asctime)s %(name)-15s [%(levelname)-8s] %(message)s'))
logger = logging.getLogger('secrets-updater')
logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
logger.addHandler(ch)

logger.info(f'Secret names will be versioned with: {TIMESTAMP}')


def create_new_secret(file, secret_name_prefix, create_unversioned=False, labels={}):
    unversioned_secret_name =   f'{secret_name_prefix}_{DOMAIN}'
    full_secret_name =          f'{secret_name_prefix}_{DOMAIN}_{TIMESTAMP}'
    if not create_unversioned:
        # Get labels from the unversioned secret so they can be copied to the new one
        for secret in client.secrets.list():
            if secret.name == unversioned_secret_name:
                labels = secret.attrs['Spec']['Labels']
                logger.info(f' - {secret.name} labels are: {labels}')
                break
        else:
            logger.warning(f' - No exsiting secret named {unversioned_secret_name} was found. It will be created.')
    with open(file) as f:
        if create_unversioned:
            new_name = unversioned_secret_name
        else:
            new_name = full_secret_name
        logger.info(f' - Creating new secret {new_name} with labels {labels} from file {file}')
        new_secret_object = client.secrets.create(name=new_name, data=f.read(), labels=labels)
    return new_secret_object, labels


# Create new timestamped secrets
changing_secrets = []
if 'KEY_SECRET' in os.environ:
    logger.info(f'Secret name for SSL Private Key will be {os.environ["KEY_SECRET"]}_{DOMAIN}_{TIMESTAMP}')
    new_key_secret, new_key_labels = create_new_secret(KEYFILE, os.environ["KEY_SECRET"])
    changing_secrets.append(f'{os.environ["KEY_SECRET"]}_{DOMAIN}')
if 'CERT_SECRET' in os.environ:
    logger.info(f'Secret name for SSL certificate will be {os.environ["CERT_SECRET"]}_{DOMAIN}_{TIMESTAMP}')
    new_cert_secret, new_cert_labels = create_new_secret(CERTFILE, os.environ["CERT_SECRET"])
    changing_secrets.append(f'{os.environ["CERT_SECRET"]}_{DOMAIN}')
if 'FULLCHAIN_SECRET' in os.environ:
    logger.info(f'Secret name for SSL full chain will be {os.environ["FULLCHAIN_SECRET"]}_{DOMAIN}_{TIMESTAMP}')
    new_fullchain_secret, new_fullchain_labels = create_new_secret(FULLCHAINFILE, os.environ["FULLCHAIN_SECRET"])
    changing_secrets.append(f'{os.environ["FULLCHAIN_SECRET"]}_{DOMAIN}')
if 'CHAIN_SECRET' in os.environ:
    logger.info(f'Secret name for SSL chain will be {os.environ["CHAIN_SECRET"]}_{DOMAIN}_{TIMESTAMP}')
    new_chain_secret, new_chain_labels = create_new_secret(CHAINFILE, os.environ["CHAIN_SECRET"])
    changing_secrets.append(f'{os.environ["CHAIN_SECRET"]}_{DOMAIN}')

logger.debug(f'All the secrets that have changed are: {changing_secrets}')

# Find services using any of the changing secrets and update them to use the new ones. (They could be using versioned or unversioned ones)
for service in client.services.list():
    logger.info(f'Inspecting service {service.name} to see if it uses any changing secrets...')
    try:
        service_secrets = [secret_name['SecretName'] for secret_name in service.attrs['Spec']['TaskTemplate']['ContainerSpec']['Secrets']]
    except KeyError:
        # Service has no secrets
        logger.info(f' - No secrets exist on {service.name}')
        continue
    changing_secrets_used_by_service = []
    for service_secret in service_secrets:
        for new_secret in changing_secrets:
            if service_secret.startswith(new_secret):
                changing_secrets_used_by_service.append(service_secret)
                break
    if changing_secrets_used_by_service:
        logger.info(f' - {service.name} uses {changing_secrets_used_by_service}. Recreating list of secrets to update the service with.')
        # Loop through all secrets used by service and build a list of `SecretReference` objects to update the service with.
        secrets = []
        for secret in service.attrs['Spec']['TaskTemplate']['ContainerSpec']['Secrets']:
            if secret['SecretName'].startswith(f'{os.environ["KEY_SECRET"]}_{DOMAIN}'):
                logger.info(f'   - {secret["SecretName"]}: Replacing SSL Key with new secret {os.environ["KEY_SECRET"]}_{DOMAIN}_{TIMESTAMP}')
                secrets.append(docker.types.SecretReference(secret_id=new_key_secret.id, secret_name=new_key_secret.name, filename=secret['File']['Name'], uid=secret['File']['UID'], gid=secret['File']['GID'], mode=secret['File']['Mode']))
                logger.debug(f'     - Result: {secrets[-1]}')
            elif secret['SecretName'].startswith(f'{os.environ["CERT_SECRET"]}_{DOMAIN}'):
                logger.info(f'   - {secret["SecretName"]}: Replacing SSL Certificate with new secret {os.environ["CERT_SECRET"]}_{DOMAIN}_{TIMESTAMP}')
                secrets.append(docker.types.SecretReference(secret_id=new_cert_secret.id, secret_name=new_cert_secret.name, filename=secret['File']['Name'], uid=secret['File']['UID'], gid=secret['File']['GID'], mode=secret['File']['Mode']))
                logger.debug(f'     - Result: {secrets[-1]}')
            elif secret['SecretName'].startswith(f'{os.environ["FULLCHAIN_SECRET"]}_{DOMAIN}'):
                logger.info(f'   - {secret["SecretName"]}: Replacing SSL Full Chain with new secret {os.environ["FULLCHAIN_SECRET"]}_{DOMAIN}_{TIMESTAMP}')
                secrets.append(docker.types.SecretReference(secret_id=new_fullchain_secret.id, secret_name=new_fullchain_secret.name, filename=secret['File']['Name'], uid=secret['File']['UID'], gid=secret['File']['GID'], mode=secret['File']['Mode']))
                logger.debug(f'     - Result: {secrets[-1]}')
            elif secret['SecretName'].startswith(f'{os.environ["CHAIN_SECRET"]}_{DOMAIN}'):
                logger.info(f'   - {secret["SecretName"]}: Replacing SSL Chain with new secret {os.environ["CHAIN_SECRET"]}_{DOMAIN}_{TIMESTAMP}')
                secrets.append(docker.types.SecretReference(secret_id=new_chain_secret.id, secret_name=new_chain_secret.name, filename=secret['File']['Name'], uid=secret['File']['UID'], gid=secret['File']['GID'], mode=secret['File']['Mode']))
                logger.debug(f'     - Result: {secrets[-1]}')
            else:
                # This is not a changing secret. Just recreate `SecretReference` object and add it to the list
                logger.debug(f'   - {secret["SecretName"]}: This secret is not a changing secret. Leaving as is.')
                secrets.append(docker.types.SecretReference(secret_id=secret['SecretID'], secret_name=secret['SecretName'], filename=secret['File']['Name'], uid=secret['File']['UID'], gid=secret['File']['GID'], mode=secret['File']['Mode']))
        logger.info(f'Updating {service.name} with new secrets: {secrets}')
        result = service.update(secrets=secrets)
        logger.debug(f'  - Result: {result}')
    else:
        logger.info(f' - {service.name} does not use any changing secrets.')
logger.info('Finished inspecting services...')


# Now that the old secrets have been replaced in all the services, delete the old secrets
for secret in client.secrets.list():
    if (('KEY_SECRET' in os.environ and secret.name.startswith(f'{os.environ["KEY_SECRET"]}_{DOMAIN}') and secret.name != f'{os.environ["KEY_SECRET"]}_{DOMAIN}_{TIMESTAMP}')
       or ('CERT_SECRET' in os.environ and secret.name.startswith(f'{os.environ["CERT_SECRET"]}_{DOMAIN}') and secret.name != f'{os.environ["CERT_SECRET"]}_{DOMAIN}_{TIMESTAMP}')
       or ('FULLCHAIN_SECRET' in os.environ and secret.name.startswith(f'{os.environ["FULLCHAIN_SECRET"]}_{DOMAIN}') and secret.name != f'{os.environ["FULLCHAIN_SECRET"]}_{DOMAIN}_{TIMESTAMP}')
       or ('CHAIN_SECRET' in os.environ and secret.name.startswith(f'{os.environ["CHAIN_SECRET"]}_{DOMAIN}') and secret.name != f'{os.environ["CHAIN_SECRET"]}_{DOMAIN}_{TIMESTAMP}')):
        logger.info(f'Removing {secret.name}')
        result = secret.remove()
        logger.debug(f'  - Result: {result}')

# Recreate the unversioned secrets with the newest data. They won't be used by now by any services, but it allows them to be referenced in compose.yml files
logger.info('Recreating unversioned secrets')
if 'KEY_SECRET' in os.environ:
    new_key_secret, _ = create_new_secret(KEYFILE, os.environ["KEY_SECRET"], labels=new_key_labels, create_unversioned=True)
    logger.debug(f'  - Result: {new_key_secret.attrs}')
if 'CERT_SECRET' in os.environ:
    new_cert_secret, _ = create_new_secret(CERTFILE, os.environ["CERT_SECRET"], labels=new_cert_labels, create_unversioned=True)
    logger.debug(f'  - Result: {new_cert_secret}')
if 'FULLCHAIN_SECRET' in os.environ:
    new_fullchain_secret, _ = create_new_secret(FULLCHAINFILE, os.environ["FULLCHAIN_SECRET"], labels=new_fullchain_labels, create_unversioned=True)
    logger.debug(f'  - Result: {new_fullchain_secret}')
if 'CHAIN_SECRET' in os.environ:
    new_chain_secret, _ = create_new_secret(CHAINFILE, os.environ["CHAIN_SECRET"], labels=new_chain_labels, create_unversioned=True)
    logger.debug(f'  - Result: {new_chain_secret}')

logger.info('All done!')

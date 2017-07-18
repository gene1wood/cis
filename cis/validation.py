import boto3
import logging
import os

from pluginbase import PluginBase
from cis.encryption import decrypt
from cis.settings import get_config


PLUGIN_BASE = PluginBase(package='cis.plugins.validation')
PLUGIN_SOURCE = PLUGIN_BASE.make_plugin_source(searchpath=[
    os.path.join(os.path.abspath(os.path.dirname(__file__)),
    'plugins/validation/')])

# List of plugins to load, in order
PLUGIN_LOAD = ['json_schema_plugin']


logger = logging.getLogger(__name__)


def validate(publisher, **payload):
    """
    Validates the payload passed to CIS.

    :payload: Encrypted payload based on the output of `cis.encryption.encrypt` method
    """

    logger.info("Attempting payload validation for publisher {}".format(publisher))

    if not publisher:
        logger.exception('No publisher provided')
        return False

    try:
        # Decrypt payload coming from CIS using KMS key
        # This ensures that publisher is trusted by CIS
        decrypted_payload = decrypt(**payload)
    except Exception:
        logger.exception('Decryption failed')
        return False

    with PLUGIN_SOURCE:
        for plugin in PLUGIN_LOAD:
            cur_plugin = PLUGIN_SOURCE.load_plugin(plugin)
            try:
                cur_plugin.run(publisher, decrypted_payload)
            except Exception:
                logger.exception('Validation plugin {} failed'.format(cur_plugin.__name__))
                return False

    return True


def retrieve_from_vault(user):
    """
    Check if a user exist in dynamodb

    :user: User's id
    """

    dynamodb = boto3.resource('dynamodb')
    config = get_config()
    dynamodb_table = config('dynamodb_table', namespace='cis')
    table = dynamodb.Table(dynamodb_table)

    try:
        response = table.get_item(Item='userid')
    except Exception:
        logger.exception('DynamoDB GET failed')
        return None
    return True


def store_to_vault(data):
    """
    Store data to DynamoDB.

    :data: Data to store in the database
    """

    dynamodb = boto3.resource('dynamodb')
    config = get_config()
    dynamodb_table = config('dynamodb_table', namespace='cis')
    table = dynamodb.Table(dynamodb_table)

    # Put data to DynamoDB
    try:
        response = table.put_item(
            Item=data
        )
    except Exception:
        logger.exception('DynamoDB PUT failed')
        return None
    return response

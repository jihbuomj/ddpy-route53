import os
import boto3
import logging
from ddpy.plugin_base import GivePluginBase

logger = logging.getLogger(__name__)

class GivePlugin(GivePluginBase):
    def __init__(self, *args, **kwargs):
        if (
            'aws_access_key_id' in args[0]
            and 'aws_secret_access_key' in args[0]
        ):
            aws_access_key_id = args[0]['aws_access_key_id']
            aws_secret_access_key = args[0]['aws_secret_access_key']
        elif (
            'DDPY_AWS_ACCESS_KEY_ID' in os.environ
            and 'DDPY_AWS_SECRET_ACCESS_KEY' in os.environ
        ):
            aws_access_key_id = os.environ.get('DDPY_AWS_ACCESS_KEY_ID')
            aws_secret_access_key = os.environ.get('DDPY_AWS_SECRET_ACCESS_KEY')
        else:
            aws_access_key_id = None
            aws_secret_access_key = None

        self.zone = args[0]['zone']
        self.domains = args[0]['domains']
        if 'comment' in args[0]:
            self.comment = args[0]['comment']
        else:
            self.comment = 'Changes made by ddpy'

        self.client = boto3.client(
            'route53',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )

    def give_data(self, ip_info):

        hosted_zones = self.client.list_hosted_zones()['HostedZones']

        for zone in hosted_zones:
            if zone['Name'] == self.zone:
                def record_set_map(domain, new_ip): return {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': domain,
                        'ResourceRecords': [
                            {
                                'Value': new_ip,
                            },
                        ],
                        'TTL': 60,
                        'Type': 'A',
                    },
                }

                changes = [record_set_map(domain, ip_info['ip'])
                           for domain in self.domains]

                change_batch = {
                    'Changes': changes,
                    'Comment': self.comment
                }
                self.client.change_resource_record_sets(
                    ChangeBatch=change_batch,
                    HostedZoneId=zone['Id']
                )
                break

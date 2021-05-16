import sys
import boto3
import docker

from re import sub
from yaml import safe_load
from base64 import b64decode
from operator import itemgetter
from os.path import normpath, join
from utils import topological_sort
from collections import defaultdict


class Deployment():
    clients = {
        'ecr': boto3.client('ecr'),
        'sts': boto3.client('sts'),
        'iam': boto3.client('iam'),
        'events': boto3.client('events'),
        'lambda': boto3.client('lambda'),
        'session': boto3.session.Session(),
        'docker': docker.client.from_env(),
        'docker.images': docker.client.from_env().images,
    }

    def __init__(self, root='.'):
        # Initialize paths and shared dictionary
        self.root = root
        self.shared = defaultdict(dict)

        # Load the config and docker images
        with open(normpath(join(self.root, 'awyes.yml'))) as config:
            self.config = safe_load(config)

        # Login to docker
        Deployment.clients['docker'].login(
            username="AWS",
            password=self.ecr_password,
            registry=f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com"
        )

    @property
    def region(self):
        return Deployment.clients['session'].region_name

    @property
    def account_id(self):
        id_response = Deployment.clients['sts'].get_caller_identity()

        return id_response['Account']

    @property
    def ecr_password(self):
        token_response = Deployment.clients['ecr'].get_authorization_token()

        get_data = itemgetter('authorizationData')
        get_token = itemgetter('authorizationToken')

        token = get_token(get_data(token_response).pop())

        return sub("AWS:", "", b64decode(token).decode())

    def deploy(self):
        # Unpack action metadata
        unpack = itemgetter('depends_on', 'output', 'args', 'client')

        # Loop over each client
        for client_name, resources in self.config.items():
            client = vars(Deployment)['clients'][client_name]

            # Loop over each resource
            for resource_name, steps in resources.items():

                # Loop over each step
                for action_name, metadata in steps.items():
                    metadata.setdefault('output', False)
                    metadata.setdefault('depends_on', [])

                    # depends_on, output, args, client = unpack(metadata)
                    # action = getattr(client, action_name)

                    print(action_name)


if __name__ == '__main__':
    _, root = sys.argv

    Deployment(root=root).deploy()

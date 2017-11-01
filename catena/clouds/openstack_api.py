# (C) Copyright 2017 Hewlett Packard Enterprise Development LP.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import uuid

import openstack.connection
from oslo_config import cfg
from oslo_log import log

from catena.common.utils import encrypt_private_rsakey

LOG = log.getLogger(__name__)
CONF = cfg.CONF


class OpenStack(object):
    @staticmethod
    def _new_id():
        return str(uuid.uuid4())

    def __init__(self, cloud):
        self.cloud = cloud
        self.connection = openstack.connection.Connection(
            verify=False,
            **cloud.get_authentication())

    def get_node_flavours(self):
        LOG.debug("Getting node flavours")

        result = []

        for flavor in self.connection.compute.flavors():
            result.append(flavor.name)

        return result

    def get_networks(self):
        LOG.debug("Getting networks")

        result = []

        for network in self.connection.network.networks():
            result.append(network.name)

        return result

    def get_instances(self):
        LOG.debug("Getting instances")

        result = []

        for server in self.connection.compute.servers():
            result.append(server.name)

        return result

    def _create_keypair(self, public_key):
        keypair_name = "catena_" + self._new_id()

        LOG.debug("Adding keypair: {}".format(keypair_name))

        keypair = self.connection.compute.create_keypair(
            name=keypair_name,
            public_key=public_key
        )

        return keypair

    def get_instance_details(self, instance_name):
        instance_light = self.connection.compute.find_server(instance_name)
        return self.connection.compute.get_server(instance_light)

    def add_node(self, public_key, flavour_name, name, chain):
        cloud_config = chain.get_cloud_config()
        provider_config = self.cloud.get_cloud_config()

        LOG.debug("Creating server")

        image_name = provider_config['image_name']

        image = self.connection.compute.find_image(image_name)
        flavor = self.connection.compute.find_flavor(flavour_name)
        keypair = self._create_keypair(public_key)

        server = self.connection.compute.create_server(
            name=name,
            image_id=image.id, flavor_id=flavor.id,
            networks=[{"uuid": cloud_config['network_id']}],
            key_name=keypair.name,
            user_data=base64.b64encode(provider_config['user_data'])
        )

        server = self.connection.compute.wait_for_server(server)

        ip = server.addresses[cloud_config['network']][0]['addr']

        import time
        time.sleep(120)

        return (server.id, ip)

    def delete_node(self, chain, id):
        self.connection.compute.delete_server(id)

    def initialize_cloud(self, chain):
        cloud_config = chain.get_cloud_config()

        assert len(cloud_config['jumpbox']) > 0, "Must specify a jumpbox"
        assert len(cloud_config['jumpbox_key']) > 0, \
            "Must specify a jumpbox ssh key"
        assert len(cloud_config['controller_flavour']) > 0, \
            "Must specify a controller flavour"

        cloud_config['jumpbox_key'] = encrypt_private_rsakey(
            cloud_config['jumpbox_key'])

        network_name = cloud_config['network']

        jumpbox_name = cloud_config['jumpbox']
        jumpbox = self.get_instance_details(jumpbox_name)
        jumpbox_ip = [network for network in jumpbox.addresses[network_name] if
                      network['OS-EXT-IPS:type'] == 'floating'][0]['addr']

        network = self.connection.network.find_network(network_name)

        cloud_config['jumpbox_ip'] = jumpbox_ip
        cloud_config['network_id'] = network.id

        chain.set_cloud_config(cloud_config)

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

import uuid

from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from msrestazure.azure_active_directory import ServicePrincipalCredentials
from oslo_config import cfg
from oslo_log import log

from catena.common.utils import encrypt_private_rsakey

LOG = log.getLogger(__name__)
CONF = cfg.CONF


class Azure(object):
    @staticmethod
    def _new_id():
        return str(uuid.uuid4())

    def __init__(self, cloud):
        self.cloud = cloud
        self.authentication = cloud.get_authentication()

        self.location = self.authentication['location']

        self.credentials = ServicePrincipalCredentials(
            client_id=self.authentication['client_id'],
            secret=self.authentication['secret'],
            tenant=self.authentication['tenant'])

        self.resource_client = ResourceManagementClient(
            self.credentials,
            str(self.authentication['subscription_id'])
        )
        self.compute_client = ComputeManagementClient(
            self.credentials,
            str(self.authentication['subscription_id'])
        )
        self.network_client = NetworkManagementClient(
            self.credentials,
            str(self.authentication['subscription_id'])
        )

    def get_node_flavours(self):
        LOG.debug("Getting node flavours")

        result = []

        for flavor in self.compute_client.virtual_machine_sizes.list(
                self.location):
            result.append(flavor.name)

        return result

    def get_networks(self):
        LOG.debug("Getting networks")

        result = []

        for network in self.network_client.virtual_networks.list_all():
            result.append(
                "{}/{}".format(network.id.split("/")[-5], network.name))

        return result

    def get_instances(self):
        LOG.debug("Getting instances")

        result = []

        for server in self.compute_client.virtual_machines.list_all():
            result.append(server.name)

        return result

    def create_vm_parameters(self, name, flavour, public_key, nic_id):
        """Create the VM parameters structure.
        """
        provider_config = self.cloud.get_cloud_config()
        return {
            'location': self.location,
            'os_profile': {
                'computer_name': self._new_id(),
                'admin_username': 'ubuntu',
                'linux_configuration': {
                    'disable_password_authentication': True,
                    'ssh': {
                        'public_keys': [
                            {
                                'path': '/home/{}/.ssh/authorized_keys'
                                        .format('ubuntu'),
                                'key_data': public_key
                            }
                        ]
                    }
                }
            },
            'hardware_profile': {
                'vm_size': flavour
            },
            'storage_profile': {
                'image_reference': provider_config['image']
            },
            'network_profile': {
                'network_interfaces': [{'id': nic_id, }]
            },
        }

    def add_node(self, public_key, flavour_name, name, chain):
        cloud_config = chain.get_cloud_config()

        LOG.debug("Creating server")

        network_name = cloud_config['network']
        resource_group = network_name.split("/")[0]

        async_nic_creation = \
            self.network_client.network_interfaces.create_or_update(
                resource_group,
                'if-{}'.format(name),
                {
                    'location': self.location,
                    'ip_configurations': [
                        {
                            'name': 'netcfg-{}'.format(name),
                            'subnet': {'id': cloud_config['network_id']}
                        }
                    ],
                    'network_security_group': {
                        'id': cloud_config['security_group']
                    }
                }
            )

        nic = async_nic_creation.result()
        vm_parameters = self.create_vm_parameters(
            name,
            flavour_name,
            public_key,
            nic.id
        )
        async_vm_creation = \
            self.compute_client.virtual_machines.create_or_update(
                resource_group,
                name,
                vm_parameters
            )
        async_vm_creation.wait()

        vm = async_vm_creation.result()
        nic = self.network_client.network_interfaces.get(
            resource_group,
            vm.network_profile.network_interfaces[0].id.split('/')[-1]
        )

        return name, nic.ip_configurations[0].private_ip_address

    def delete_node(self, chain, id):
        cloud_config = chain.get_cloud_config()

        network_name = cloud_config['network']
        resource_group = network_name.split("/")[0]

        vm = self.compute_client.virtual_machines.get(resource_group, id)
        disk_name = vm.storage_profile.os_disk.name
        nic_name = vm.network_profile.network_interfaces[0].id.split('/')[-1]

        self.compute_client.virtual_machines.delete(
            resource_group,
            vm.name
        ).wait()
        self.compute_client.disks.delete(resource_group, disk_name)
        self.network_client.network_interfaces.delete(resource_group, nic_name)

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
        resource_group = network_name.split("/")[0]

        vm_jumpbox = self.compute_client.virtual_machines.get(
            resource_group,
            cloud_config['jumpbox']
        )

        nic = self.network_client.network_interfaces.get(
            resource_group,
            vm_jumpbox.network_profile.network_interfaces[0].id.split('/')[-1]
        )
        ip_config = nic.ip_configurations[0]
        public_ip = self.network_client.public_ip_addresses.get(
            resource_group,
            ip_config.public_ip_address.id.split('/')[-1]
        )

        cloud_config['jumpbox_ip'] = public_ip.ip_address
        cloud_config['network_id'] = ip_config.subnet.id
        cloud_config['security_group'] = nic.network_security_group.id

        chain.set_cloud_config(cloud_config)

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

from oslo_config import cfg
from oslo_db.sqlalchemy import enginefacade

from catena.chain_backends.ethereum import ethereum_api as chain_api
from catena.clouds.azure_api import Azure
from catena.clouds.openstack_api import OpenStack
from catena.common.utils import create_and_encrypt_sshkey
from catena.db.sqlalchemy import api as db_api

CONF = cfg.CONF

CLOUDS = {'openstack': OpenStack, 'azure': Azure}


def get_cloud_types():
    return CLOUDS.keys()


def get_clouds():
    context = db_api.get_context()
    clouds = db_api.get_clouds(context)
    result = [_cleanup_cloud(cloud) for cloud in clouds]

    return result


def _cleanup_cloud(cloud):
    # This is a white-list because we have secrets (like ssh keys) in the db
    #  that shouldn't be exposed

    return {
        'cloud_config': cloud['cloud_config'],
        'id': cloud['id'],
        'name': cloud['name'],
        'created_at': cloud['created_at'],
        'updated_at': cloud['updated_at'],
    }


def get_cloud_api_by_model(cloud):
    return CLOUDS[cloud.type](cloud)


def get_cloud_api(cloud_id):
    context = db_api.get_context()
    cloud = db_api.get_cloud(context, cloud_id)
    return get_cloud_api_by_model(cloud)


def create_cloud(type, name, authentication, config):
    context = db_api.get_context()

    with enginefacade.writer.using(context):
        cloud = db_api.create_cloud(context, type)
        cloud.set_authentication(authentication)
        cloud.name = name
        cloud.set_cloud_config(config)
        cloud.save(context)

    return cloud


def create_node(blockchain_id, data):
    context = db_api.get_context()

    with enginefacade.writer.using(context):
        blockchain = db_api.get_chain(context, blockchain_id)
        controller_node = db_api.get_controller_node(context, blockchain)
        cloud_api = get_cloud_api_by_model(blockchain.cloud)

        public_key, encrypted_key = create_and_encrypt_sshkey()

        id, ip = cloud_api.add_node(public_key, data['flavour'], data['name'],
                                    blockchain)
        node = db_api.create_node(context, id, blockchain, ip, encrypted_key,
                                  data['type'], data['name'])
        node_id = chain_api.provision_node(blockchain, node,
                                           blockchain.get_cloud_config()[
                                               'jumpbox_ip'],
                                           controller_node.ip)
        chain_config = {'eth_node_id': node_id.split('"')[1]}
        node.set_chain_config(chain_config)
        node.save(context)

    return node


def delete_node(blockchain_id, node_id):
    context = db_api.get_context()

    with enginefacade.writer.using(context):
        blockchain = db_api.get_chain(context, blockchain_id)
        node = db_api.get_node(context, blockchain, node_id)
        if node.type != 'controller':
            cloud_api = get_cloud_api(blockchain.cloud_id)
            cloud_api.delete_node(blockchain, node.id)
            node.delete(context)


def get_nodes(blockchain_id):
    context = db_api.get_context()

    with enginefacade.reader.using(context):
        blockchain = db_api.get_chain(context, blockchain_id)

        result = [_cleanup_node_data(node) for node in blockchain.nodes]

        return result


def get_node(blockchain_id, node_id):
    context = db_api.get_context()

    with enginefacade.reader.using(context):
        blockchain = db_api.get_chain(context, blockchain_id)
        node = db_api.get_node(context, blockchain, node_id)

        return _cleanup_node_data(node)


def _cleanup_node_data(node):
    # This is a white-list because we have secrets (like ssh keys) in the db
    #  that shouldn't be exposed

    return {
        'chain_config': node['chain_config'],
        'ip': node['ip'],
        'id': node['id'],
        'name': node['name'],
        'type': node['type'],
        'chain_id': node['chain_id'],
        'created_at': node['created_at'],
        'updated_at': node['updated_at'],
    }


def get_backend_info():
    return chain_api.get_backend_info()


def create_chain(cloud_id, name, new_chain_config, new_cloud_config):
    assert len(name) > 0, "Must specify a name"

    context = db_api.get_context()

    with enginefacade.writer.using(context):
        cloud = db_api.get_cloud(context, cloud_id)

        cloud_api = get_cloud_api_by_model(cloud)

        chain = db_api.create_chain(context, name, "ethereum", cloud,
                                    new_chain_config, new_cloud_config)
        chain_api.initialize_chain(chain)
        cloud_api.initialize_cloud(chain)
        chain.save(context)

        cloud_config = chain.get_cloud_config()
        chain_config = chain.get_chain_config()

        controller_name = chain.name + "_controller"

        public_key, encrypted_key = create_and_encrypt_sshkey()

        id, ip = cloud_api.add_node(public_key,
                                    cloud_config['controller_flavour'],
                                    controller_name, chain)

        node = db_api.create_node(context, id=id, chain=chain, ip=ip,
                                  ssh_key=encrypted_key,
                                  name=chain.name + '_controller',
                                  type='controller')

        node_id = chain_api.provision_controller(chain, node,
                                                 cloud_config['jumpbox_ip'])
        chain_config = {'eth_node_id': node_id.split('"')[1]}
        node.set_chain_config(chain_config)
        node.save(context)

    return chain


def get_chains():
    context = db_api.get_context()
    chains = db_api.get_chains(context)

    result = [_cleanup_chain_data(chain) for chain in chains]

    return result


def get_chain(chain_id):
    context = db_api.get_context()
    chain = db_api.get_chain(context, chain_id)

    return _cleanup_chain_data(chain)


def _cleanup_chain_data(chain):
    # This is a white-list because we have secrets (like ssh keys) in the db
    #  that shouldn't be exposed

    return {
        'chain_backend': chain['chain_backend'],
        'chain_config': chain['chain_config'],
        'id': chain['id'],
        'cloud_id': chain['cloud_id'],
        'name': chain['name'],
        'created_at': chain['created_at'],
        'updated_at': chain['updated_at'],
    }


def delete_chain(chain_id):
    context = db_api.get_context()

    with enginefacade.writer.using(context):
        chain = db_api.get_chain(context, chain_id)
        nodes = db_api.get_nodes(context, chain)
        cloud_api = get_cloud_api(chain.cloud_id)
        for node in nodes:
            cloud_api.delete_node(chain, node['id'])
        chain.delete(context)


def get_node_flavours(cloud_id):
    return get_cloud_api(cloud_id).get_node_flavours()


def get_networks(cloud_id):
    return get_cloud_api(cloud_id).get_networks()


def get_instances(cloud_id):
    return get_cloud_api(cloud_id).get_instances()

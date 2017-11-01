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

import json

from oslo_db.sqlalchemy import enginefacade
from oslo_log import log as logging

from catena.db.sqlalchemy import models

LOG = logging.getLogger(__name__)


# See documentation: https://docs.openstack.org/oslo.db/latest/user/usage
# .html#session-handling

@enginefacade.transaction_context_provider
class MyContext(object):
    "User-defined context class."


def get_context():
    return MyContext()


@enginefacade.reader
def get_chains(context, filters=None, marker=None, limit=None, sort_key=None,
               sort_dir=None):
    sort_key = ['created_at'] if not sort_key else sort_key
    if not sort_dir:
        sort_dir = 'desc'

    filters = filters or {}
    chains = []
    chains_query = context.session.query(models.Chain)
    for chain in chains_query.all():
        chain = chain.to_dict()
        chains.append(chain)
    return chains


@enginefacade.reader
def get_chain(context, chain_id):
    blockchain = context.session.query(models.Chain).get(chain_id)
    return blockchain


@enginefacade.reader
def get_nodes(context, chain, raw=False):
    nodes = []
    nodes_query = context.session.query(models.ChainNodes).filter(
        models.ChainNodes.chain_id == chain.id)
    if raw:
        return nodes_query
    for node in nodes_query.all():
        node = node.to_dict()
        nodes.append(node)
    return nodes


@enginefacade.writer
def create_chain(context, name, backend, cloud, chain_config, cloud_config):
    chain_ref = models.Chain()
    chain_ref.name = name
    chain_ref.chain_backend = backend
    chain_ref.cloud = cloud
    chain_ref.chain_config = json.dumps(chain_config)
    chain_ref.cloud_config = json.dumps(cloud_config)
    chain_ref.owner = 'saad'
    chain_ref.status = 'creating'

    chain_ref.save(context)
    return chain_ref


@enginefacade.writer
def create_node(context, id, chain, ip, ssh_key, name, type):
    node_ref = models.ChainNodes()
    node_ref.id = id
    node_ref.chain = chain
    node_ref.ip = ip
    node_ref.ssh_key = ssh_key
    node_ref.name = name
    node_ref.type = type

    node_ref.save(context)
    return node_ref


@enginefacade.reader
def get_node(context, chain, node_id):
    return context.session.query(models.ChainNodes).get(node_id)


@enginefacade.reader
def get_controller_node(context, chain):
    return context.session.query(models.ChainNodes).filter(
        models.ChainNodes.chain_id == chain.id).filter(
        models.ChainNodes.type == 'controller').one()


@enginefacade.reader
def get_clouds(context, filters=None, marker=None, limit=None, sort_key=None,
               sort_dir=None):
    sort_key = ['created_at'] if not sort_key else sort_key
    if not sort_dir:
        sort_dir = 'desc'

    filters = filters or {}
    chains = []
    chains_query = context.session.query(models.Cloud)
    for chain in chains_query.all():
        chain = chain.to_dict()
        chains.append(chain)
    return chains


@enginefacade.reader
def get_cloud(context, cloud_id):
    return context.session.query(models.Cloud).get(cloud_id)


@enginefacade.writer
def create_cloud(context, type):
    cloud_ref = models.Cloud()
    cloud_ref.type = type

    cloud_ref.save(context)
    return cloud_ref

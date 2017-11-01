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
import os
import random
import string
import sys
import tempfile

from oslo_log import log

from catena.common import ansible_utils
from catena.common.utils import decrypt_private_rsakey

CHAIN_TYPES = ['proof-of-work']
NODE_TYPES = ['miner']

LOG = log.getLogger(__name__)


def initialize_chain(chain):
    chain_config = chain.get_chain_config()

    assert (chain_config['type'] in CHAIN_TYPES) or (
        chain_config.get('network_id', None) and chain_config.get('genesis',
                                                                  None))
    assert len(
        chain_config['mining_account']) > 0, "Must specify a mining account"

    # Only assign network_id and genesis if they are not already provided by
    #  the user (i.e. to connect to an existing blockchain)

    if not chain_config.get('network_id', None):
        # Network id must be unqiue per blockchain network. A collision is
        # very unlikely because private blockchains
        # are typically deployed in their own networks and even if they are
        # in the same network: the math works in our favour
        chain_config['network_id'] = random.randint(5000, sys.maxint)

    if not chain_config.get('genesis', None):
        if chain_config['type'] == 'proof-of-work':
            chain_config['genesis'] = {
                "alloc": {},
                "config": {
                    # Chain id is used to prevent replay attacks. MetaMask
                    # currently has a bug
                    # because it assumes network_id == chain_id. To avoid
                    # triggering this bug
                    # we set the chain id accordingly.
                    # https://ethereum.stackexchange.com/questions/26/what-is-a
                    # -replay-attack
                    # https://github.com/ethereum/eips/issues/155
                    # https://github.com/MetaMask/metamask-extension/issues
                    # /1722
                    "chainId": chain_config['network_id'],
                    "homesteadBlock": 0,
                    "eip155Block": 0,
                    "eip158Block": 0
                },
                "nonce": "0x0000000000000042",
                "difficulty": "0x6666",
                "mixhash": "0x0000000000000000000000000000000000000000000000000000000000000000",  # noqa
                "coinbase": "0x0000000000000000000000000000000000000000",
                "timestamp": "0x00",
                "parentHash": "0x0000000000000000000000000000000000000000000000000000000000000000",  # noqa
                "extraData": "0x11bbe8db4e347b4e8c937c1c8370e4b5ed33adb3db69cbdb7a38e1e50b1b82fa",  # noqa
                "gasLimit": "0x4c4b40"
                }
        else:
            raise Exception('Unkown chain type for ethereum: {}'.format(
                chain_config['type']))

    chain_config['stats_secret'] = ''.join(
        random.choice(string.ascii_lowercase + string.digits) for _ in
        range(16))

    chain.set_chain_config(chain_config)


def _write_genesis(node, file):
    LOG.debug("Write genesis file to {}".format(file.name))
    genesis_json = node.chain.get_chain_config()['genesis']
    json.dump(genesis_json, file)
    file.flush()


def generate_ansible_config(provider_config, cloud_config, chain_config):
    config = {
        "network_id": chain_config['network_id'],
        "stats_secret": chain_config['stats_secret'],
        }

    if "proxy" in provider_config:
        config["proxy_env"] = {
            "http_proxy": provider_config["proxy"],
            "https_proxy": provider_config["proxy"],
            "ftp_proxy": provider_config["proxy"],
            "no_proxy": "localhost,127.0.0.1"
            }
    else:
        config["proxy_env"] = {}

    return config


def provision_controller(chain, node, jumpbox_ip):
    chain_config = chain.get_chain_config()
    cloud_config = chain.get_cloud_config()
    provider_config = chain.cloud.get_cloud_config()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    playbook_path = os.path.join(dir_path, 'ansible', 'deploy-controller.yml')
    node_id_file = os.path.join('/tmp', 'ansible_node_id_' + node.id)

    config = generate_ansible_config(provider_config, cloud_config,
                                     chain_config)

    with tempfile.NamedTemporaryFile() as temp_genesis:
        _write_genesis(node, temp_genesis)

        home = os.path.expanduser("~/.ssh")

        # We can assume that this is safe because Python makes use of O_EXCL:
        # https://docs.python.org/2/library/tempfile.html#tempfile.mkstemp
        with tempfile.NamedTemporaryFile(dir=home) as temp_node_ssh, \
                tempfile.NamedTemporaryFile(dir=home) as temp_jumpbox_ssh:
            node.get_ssh_key(temp_node_ssh)
            decrypt_private_rsakey(cloud_config['jumpbox_key'],
                                   temp_jumpbox_ssh)
            LOG.debug(
                "Writing node key to {}. Writing jumbox key to {}".format(
                    temp_node_ssh.name, temp_jumpbox_ssh.name))

            config["genesis_file"] = temp_genesis.name
            config["node_id_file"] = node_id_file

            ansible_utils.launch_playbook(playbook_path, temp_node_ssh.name,
                                          [node.ip], config, jumpbox_ip,
                                          temp_jumpbox_ssh.name)
    try:
        with open(node_id_file, 'r') as node_id:
            return node_id.read()
    finally:
        os.unlink(node_id_file)


def _get_bootnodes(chain):
    chain_config = chain.get_chain_config()
    bootnodes = chain_config.get('external_bootnodes', [])
    if bootnodes is None:
        bootnodes = []

    for node in chain.nodes:
        node_chain_config = node.get_chain_config()

        if 'eth_node_id' in node_chain_config:  # Nodes that are currently
            # provisioned may not have a enode id yet
            bootnodes.append(
                'enode://{}@{}:30303'.format(node_chain_config['eth_node_id'],
                                             node.ip))

    return ",".join(bootnodes)


def provision_node(chain, node, jumpbox_ip, controller_ip):
    chain_config = chain.get_chain_config()
    cloud_config = chain.get_cloud_config()
    provider_config = chain.cloud.get_cloud_config()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    playbook_path = os.path.join(dir_path, 'ansible', 'deploy-geth.yml')
    node_id_file = os.path.join('/tmp', 'ansible_node_id_' + node.id)
    bootnodes = _get_bootnodes(chain)

    config = generate_ansible_config(provider_config, cloud_config,
                                     chain_config)

    with tempfile.NamedTemporaryFile() as temp_genesis:
        _write_genesis(node, temp_genesis)

        home = os.path.expanduser("~/.ssh")

        # We can assume that this is safe because Python makes use of O_EXCL:
        # https://docs.python.org/2/library/tempfile.html#tempfile.mkstemp
        with tempfile.NamedTemporaryFile(
                dir=home) as temp_node_ssh, tempfile.NamedTemporaryFile(
            dir=home) as temp_jumpbox_ssh:
            node.get_ssh_key(temp_node_ssh)
            decrypt_private_rsakey(cloud_config['jumpbox_key'],
                                   temp_jumpbox_ssh)
            LOG.debug(
                "Writing node key to {}. Writing jumbox key to {}".format(
                    temp_node_ssh.name, temp_jumpbox_ssh.name))

            config["genesis_file"] = temp_genesis.name
            config["node_id_file"] = node_id_file
            config["stats_ip"] = controller_ip
            config["bootnodes"] = bootnodes
            config["etherbase"] = chain_config['mining_account']

            ansible_utils.launch_playbook(playbook_path, temp_node_ssh.name,
                                          [node.ip], config, jumpbox_ip,
                                          temp_jumpbox_ssh.name)

    try:
        with open(node_id_file, 'r') as node_id:
            return node_id.read()
    finally:
        os.unlink(node_id_file)


def get_backend_info():
    return {"ethereum": {"chain_types": CHAIN_TYPES, "node_types": NODE_TYPES}}

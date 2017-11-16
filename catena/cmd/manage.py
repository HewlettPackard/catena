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

from __future__ import print_function

import os
import subprocess
import sys
import tempfile

from oslo_config import cfg
from oslo_db.sqlalchemy import enginefacade
from oslo_log import log

from catena.common import config
from catena.common.utils import decrypt_private_rsakey
from catena.common.utils import decrypt_rsakey
from catena.db.sqlalchemy import api as db_api
from catena.db.sqlalchemy import models

CONF = cfg.CONF
LOG = log.getLogger(__name__)


def register_models():
    context = enginefacade.writer.get_engine()
    return models.register_models(context)


def unregister_models():
    context = enginefacade.writer.get_engine()
    return models.unregister_models(context)


def output_ssh_key():
    context = db_api.get_context()
    chain = db_api.get_chain(context, CONF.sub.chain_id)
    if chain is None:
        return LOG.error('This chain-id does not exist')

    node = db_api.get_node(context, chain, CONF.sub.node_id)
    if node is None:
        return LOG.error('This node-id does not exist')
    print(decrypt_rsakey(node.ssh_key))


def open_ssh_connection():
    context = db_api.get_context()

    chain = db_api.get_chain(context, CONF.sub.chain_id)
    if chain is None:
        return LOG.error('This chain-id does not exist')

    node = db_api.get_node(context, chain, CONF.sub.node_id)
    if node is None:
        return LOG.error('This node-id does not exist')

    home = os.path.expanduser("~/.ssh")

    jumpbox_ip = chain.get_cloud_config()['jumpbox_ip']

    with tempfile.NamedTemporaryFile(
            dir=home) as temp_node_ssh, tempfile.NamedTemporaryFile(
        dir=home) as temp_jumpbox_ssh:
        decrypt_private_rsakey(node.ssh_key, temp_node_ssh)
        decrypt_private_rsakey(
            chain.get_cloud_config()['jumpbox_key'],
            temp_jumpbox_ssh
        )

        args = [
            '/bin/bash', '-c',
            'ssh -i {} -o ProxyCommand="ssh -q -i {} -W %h:%p ubuntu@{}" -o '
            'StrictHostKeyChecking=no ubuntu@{}'.format(
                temp_node_ssh.name,
                temp_jumpbox_ssh.name,
                jumpbox_ip,
                node.ip)
        ]

        process = subprocess.Popen(args)
        process.wait()


def register_sub_opts(subparser):
    parser = subparser.add_parser('db_sync')
    parser.set_defaults(action_fn=register_models)
    parser.set_defaults(action='db_sync')

    parser = subparser.add_parser('db_remove')
    parser.set_defaults(action_fn=unregister_models)
    parser.set_defaults(action='db_remove')

    parser = subparser.add_parser('ssh_key')
    parser.add_argument('chain_id')
    parser.add_argument('node_id')
    parser.set_defaults(action_fn=output_ssh_key)
    parser.set_defaults(action='ssh_key')

    parser = subparser.add_parser('ssh')
    parser.add_argument('chain_id')
    parser.add_argument('node_id')
    parser.set_defaults(action_fn=open_ssh_connection)
    parser.set_defaults(action='ssh')


SUB_OPTS = [
    cfg.SubCommandOpt(
        'sub',
        dest='sub',
        title='Sub Options',
        handler=register_sub_opts)
]


def main():
    """Parse options and call the appropriate class/method."""
    CONF.register_cli_opts(SUB_OPTS)
    config.parse_args(sys.argv[1:])
    config.setup_logging()
    try:
        if CONF.sub.action.startswith('db'):
            return CONF.sub.action_fn()
        if CONF.sub.action.startswith('ssh'):
            return CONF.sub.action_fn()
    except Exception as e:
        sys.exit("ERROR: {0}".format(e))

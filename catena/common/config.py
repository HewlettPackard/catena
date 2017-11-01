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
from oslo_log import log

from catena import __version__ as CATENA_VERSION

CONF = cfg.CONF
LOG = log.getLogger(__name__)

_OPTS = [cfg.IPOpt('host', default="0.0.0.0",
                   help="The IP address to be used to bind the web server"),
         cfg.PortOpt('port', default=1989,
                     help="Port to access the webservice"),
         cfg.StrOpt('encryption_key', required=True,
                    help="The encryption key for the ssh key files"),
         cfg.StrOpt('base_image', default="Catena",
                    help="The image used when provisioning new nodes. "
                         "Currently only "
                         "Ubuntu 16.04 is supported.")]


def parse_args(args=[]):
    CONF.register_opts(_OPTS)
    CONF.register_cli_opts(_OPTS)
    #    grp = cfg.OptGroup('jenkins', 'Jenkins configuration')
    #    CONF.register_group(grp)
    #    CONF.register_opts(_JENKINS, 'jenkins')
    log.register_options(CONF)
    default_config_files = cfg.find_config_files('catena', 'api')

    CONF(args=args, project='catena',
         default_config_files=default_config_files, version=CATENA_VERSION)

    assert len(CONF.get('encryption_key')) >= 4, \
        'encryption_key must be at least 4 characters long'


def setup_logging():
    _DEFAULT_LOG_LEVELS = ['amqp=WARN', 'amqplib=WARN', 'boto=WARN',
                           'stevedore=WARN', 'oslo_log=INFO', 'iso8601=WARN',
                           'websocket=WARN',
                           'requests.packages.urllib3.connectionpool=WARN',
                           'urllib3.connectionpool=WARN']
    _DEFAULT_LOGGING_CONTEXT_FORMAT = ('%(asctime)s.%(msecs)03d %(process)d '
                                       '%(levelname)s %(name)s [%(request_id)s'
                                       ' %(user_identity)s] %(instance)s '
                                       '%(message)s')
    log.set_defaults(_DEFAULT_LOGGING_CONTEXT_FORMAT, _DEFAULT_LOG_LEVELS)
    log.setup(CONF, 'catena', version=CATENA_VERSION)


def list_opts():
    return {None: _OPTS}.items()

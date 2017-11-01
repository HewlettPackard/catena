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

import sys
from wsgiref import simple_server

from oslo_config import cfg
from oslo_log import log

from catena.api import app
from catena.common import config

CONF = cfg.CONF
LOG = log.getLogger(__name__)


def main():
    config.parse_args(args=sys.argv[1:])
    config.setup_logging()
    ip = CONF.get('host', '0.0.0.0')
    port = CONF.get('port', 1999)
    application = app.configure_application()
    try:
        httpd = simple_server.make_server(ip, int(port), application)
        message = ('Server listening on %(ip)s:%(port)s' % {
            'ip': ip,
            'port': port
        })
        LOG.info(message)
        print(message)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Thank You ! \nBye.")
        sys.exit(0)

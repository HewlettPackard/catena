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


from catena.api.common import middleware
from catena.api import v1
import falcon
from oslo_log import log

LOG = log.getLogger(__name__)


def configure_application():
    LOG.debug("Build wsgi application.")
    middleware_list = [middleware.RequireJSON(), middleware.JSONTranslator()]
    app = falcon.API(middleware=middleware_list)

    endpoint_catalog = [
        ('/v1', v1.public_endpoints()),
        ('/', [('', v1.Resource())])
    ]

    for version_path, endpoints in endpoint_catalog:
        for route, resource in endpoints:
            app.add_route(version_path + route, resource)

    return app

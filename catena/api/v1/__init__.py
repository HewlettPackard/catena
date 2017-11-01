# Copyright (c) 2016-2017 Hewlett-Packard Development Company, L.P.
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

import falcon

from catena.api.v1 import backends
from catena.api.v1 import chains
from catena.api.v1 import cloud
from catena.api.v1 import homedoc
from catena.api.v1 import nodes

VERSION = {
    'id': 'v1',
    'status': 'CURRENT',
    'updated': '2015-05-03T13:45:00',
    'links': [{'href': '{0}v1/', 'rel': 'self'}]}

VERSIONS = {'versions': []}


def public_endpoints():
    return [
        ('/', homedoc.Resource()),

        ('/clouds', cloud.CloudResource()),
        ('/clouds/types', cloud.CloudTypesResource()),
        ('/clouds/{cloud_id}/node_flavours', cloud.CloudFlavourResource()),
        ('/clouds/{cloud_id}/networks', cloud.CloudNetworkResource()),
        ('/clouds/{cloud_id}/instances', cloud.CloudInstanceResource()),

        ('/chains', chains.ChainsResource()),
        ('/chains/{chain_id}', chains.ChainsGetResource()),

        ('/chains/{chain_id}/nodes', nodes.NodeResource()),
        ('/chains/{chain_id}/nodes/{node_id}', nodes.NodeGetResource()),

        ('/backends', backends.BackendResource()),
    ]


class Resource(object):
    def __build_versions(self, host_url):
        VERSION['links'][0]['href'] = VERSION['links'][0]['href'].format(
            host_url)
        VERSIONS['versions'] = [VERSION]

        return json.dumps(VERSIONS, ensure_ascii=False)

    def on_get(self, req, resp):
        resp.data = self.__build_versions(req.url)

        resp.status = falcon.HTTP_300

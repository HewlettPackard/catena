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


import falcon
from oslo_log import log

from catena.api.common import utils
from catena.service import service

LOG = log.getLogger(__name__)


class CloudResource(utils.BaseResource):
    def on_get(self, req, resp):
        result = service.get_clouds()

        resp.status = falcon.HTTP_200
        resp.data = result

    def on_post(self, req, resp):
        data = self.json_body(req)
        service.create_cloud(
            data['type'],
            data['name'],
            data['authentication'],
            data['config']
        )

        resp.status = falcon.HTTP_202


class CloudTypesResource(utils.BaseResource):
    def on_get(self, req, resp):
        LOG.debug("Listing all cloud types")

        types = service.get_cloud_types()

        resp.status = falcon.HTTP_200
        resp.data = types


class CloudFlavourResource(utils.BaseResource):
    def on_get(self, req, resp, cloud_id):
        LOG.debug("Listing all node flavours")

        flavours = service.get_node_flavours(cloud_id)

        resp.status = falcon.HTTP_200
        resp.data = flavours


class CloudNetworkResource(utils.BaseResource):
    def on_get(self, req, resp, cloud_id):
        LOG.debug("Listing all networks")

        networks = service.get_networks(cloud_id)

        resp.status = falcon.HTTP_200
        resp.data = networks


class CloudInstanceResource(utils.BaseResource):
    def on_get(self, req, resp, cloud_id):
        LOG.debug("Listing all instances")

        networks = service.get_instances(cloud_id)

        resp.status = falcon.HTTP_200
        resp.data = networks

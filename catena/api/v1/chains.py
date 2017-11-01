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


class ChainsResource(utils.BaseResource):
    def on_post(self, req, resp):
        LOG.debug("Creating a new blockchain")

        data = self.json_body(req)
        service.create_chain(
            data['cloud_id'],
            data['name'],
            data['chain_config'],
            data['cloud_config']
        )

        resp.status = falcon.HTTP_202

    def on_get(self, req, resp):
        LOG.debug("Listing all chains")

        result = service.get_chains()

        resp.status = falcon.HTTP_200
        resp.data = result


class ChainsGetResource(utils.BaseResource):
    def on_get(self, req, resp, chain_id):
        LOG.debug("Get chain: {}".format(chain_id))

        result = service.get_chain(chain_id)

        resp.status = falcon.HTTP_200
        resp.data = result

    def on_delete(self, req, resp, chain_id):
        LOG.debug("Delete chain: {}".format(chain_id))

        service.delete_chain(chain_id)
        resp.status = falcon.HTTP_200
        resp.data = {}

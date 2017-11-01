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


class NodeGetResource(utils.BaseResource):
    def on_get(self, req, resp, chain_id, node_id):
        result = service.get_node(chain_id, node_id)

        resp.status = falcon.HTTP_200
        resp.data = result

    def on_delete(self, req, resp, chain_id, node_id):
        service.delete_node(chain_id, node_id)
        resp.status = falcon.HTTP_202


class NodeResource(utils.BaseResource):
    def on_post(self, req, resp, chain_id):
        LOG.debug("Adding a new node")

        data = self.json_body(req)
        service.create_node(chain_id, data)

        resp.status = falcon.HTTP_202

    def on_get(self, req, resp, chain_id):
        result = service.get_nodes(chain_id)

        resp.status = falcon.HTTP_202
        resp.data = result

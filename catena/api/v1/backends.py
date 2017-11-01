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


class BackendResource(utils.BaseResource):
    def on_get(self, req, resp):
        LOG.debug("Returning backend infos")

        result = service.get_backend_info()

        resp.status = falcon.HTTP_200
        resp.data = result

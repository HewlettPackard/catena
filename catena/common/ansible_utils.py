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
import subprocess

from oslo_log import log

LOG = log.getLogger(__name__)


def execute(cmd):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True,
                             universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def launch_playbook(playbook, private_key_file, hosts, ansible_vars,
                    jumpbox_ip, jumpbox_key):
    host_list = ",".join(hosts) + ","  # Needs a trailing comma
    extra_vars = json.dumps(ansible_vars, ensure_ascii=False)
    ssh_args = '-o ProxyCommand="ssh -q -i \\"{}\\" -W %h:%p ubuntu@{}" -o ' \
               'StrictHostKeyChecking=no'.format(jumpbox_key, jumpbox_ip)
    playbook_path = os.path.join(os.path.dirname(__file__), playbook)

    command = ["ansible-playbook", playbook_path, "-i", host_list,
               "--user=ubuntu", "--private-key={}".format(private_key_file),
               "--ssh-common-args='{}'".format(ssh_args),
               "--extra-vars='{}'".format(extra_vars)]

    LOG.debug("Running: {}".format(" ".join(command)))

    for stdout_line in execute(" ".join(command)):
        LOG.debug(stdout_line.strip())

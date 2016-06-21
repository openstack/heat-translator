# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

# NOTE(aloga): this should be safe. If we do not have the clients, we won't
# have the session below, therefore the clients won't be ever called.
try:
    import novaclient.client
except ImportError:
    pass

log = logging.getLogger('heat-translator')


_FLAVORS = {
    'm1.xlarge': {'mem_size': 16384, 'disk_size': 160, 'num_cpus': 8},
    'm1.large': {'mem_size': 8192, 'disk_size': 80, 'num_cpus': 4},
    'm1.medium': {'mem_size': 4096, 'disk_size': 40, 'num_cpus': 2},
    'm1.small': {'mem_size': 2048, 'disk_size': 20, 'num_cpus': 1},
    'm1.tiny': {'mem_size': 512, 'disk_size': 1, 'num_cpus': 1},
    'm1.micro': {'mem_size': 128, 'disk_size': 0, 'num_cpus': 1},
    'm1.nano': {'mem_size': 64, 'disk_size': 0, 'num_cpus': 1}
}

SESSION = None


def get_flavors():
    ret = {}
    if SESSION is not None:
        try:
            client = novaclient.client.Client("2", session=SESSION)
        except Exception as e:
            # Handles any exception coming from openstack
            log.warn(_('Choosing predefined flavors since received '
                       'Openstack Exception: %s') % str(e))
        else:
            for flv in client.flavors.list(detailed=True):
                ret[str(flv.name)] = {
                    "mem_size": flv.ram,
                    "disk_size": flv.disk,
                    "num_cpus": flv.vcpus
                }
    return ret or _FLAVORS

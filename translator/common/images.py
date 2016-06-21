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
    import glanceclient.client
except ImportError:
    pass

log = logging.getLogger('heat-translator')


_IMAGES = {
    'ubuntu-software-config-os-init': {'architecture': 'x86_64',
                                       'type': 'Linux',
                                       'distribution': 'Ubuntu',
                                       'version': '14.04'},
    'ubuntu-12.04-software-config-os-init': {'architecture': 'x86_64',
                                             'type': 'Linux',
                                             'distribution': 'Ubuntu',
                                             'version': '12.04'},
    'fedora-amd64-heat-config': {'architecture': 'x86_64',
                                 'type': 'Linux',
                                 'distribution': 'Fedora',
                                 'version': '18.0'},
    'F18-x86_64-cfntools': {'architecture': 'x86_64',
                            'type': 'Linux',
                            'distribution': 'Fedora',
                            'version': '19'},
    'Fedora-x86_64-20-20131211.1-sda': {'architecture': 'x86_64',
                                        'type': 'Linux',
                                        'distribution': 'Fedora',
                                        'version': '20'},
    'cirros-0.3.1-x86_64-uec': {'architecture': 'x86_64',
                                'type': 'Linux',
                                'distribution': 'CirrOS',
                                'version': '0.3.1'},
    'cirros-0.3.2-x86_64-uec': {'architecture': 'x86_64',
                                'type': 'Linux',
                                'distribution': 'CirrOS',
                                'version': '0.3.2'},
    'rhel-6.5-test-image': {'architecture': 'x86_64',
                            'type': 'Linux',
                            'distribution': 'RHEL',
                            'version': '6.5'}
}

SESSION = None


def get_images():
    ret = {}

    if SESSION is not None:
        try:
            client = glanceclient.client.Client("2", session=SESSION)
        except Exception as e:
            # Handles any exception coming from openstack
            log.warn(_('Choosing predefined images since received '
                       'Openstack Exception: %s') % str(e))
        else:
            for image in client.images.list():
                metadata = ["architecture", "type", "distribution", "version"]
                if any(key in image.keys() for key in metadata):
                    ret = [image["name"]] = {}
                    for key in metadata:
                        if key in image.keys():
                            ret[image["name"]][key] = image[key]
    return ret or _IMAGES

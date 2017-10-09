
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

try:
    import glanceclient.client
    client_available = True
except ImportError:
    client_available = False
    pass

log = logging.getLogger('heat-translator')


PREDEF_IMAGES = {
    'ubuntu-software-config-os-init': {'architecture': 'x86_64',
                                       'os_type': 'linux',
                                       'os_distro': 'ubuntu',
                                       'os_version': '14.04'
                                       },

    'ubuntu-12.04-software-config-os-init': {'architecture': 'x86_64',
                                             'os_type': 'linux',
                                             'os_distro': 'ubuntu',
                                             'os_version': '12.04'
                                             },
    'fedora-amd64-heat-config': {'architecture': 'x86_64',
                                 'os_type': 'linux',
                                 'os_distro': 'fedora',
                                 'os_version': '18.0'
                                 },
    'F18-x86_64-cfntools': {'architecture': 'x86_64',
                            'os_type': 'linux',
                            'os_distro': 'fedora',
                            'os_version': '19'
                            },
    'Fedora-x86_64-20-20131211.1-sda': {'architecture': 'x86_64',
                                        'os_type': 'linux',
                                        'os_distro': 'fedora',
                                        'os_version': '20'
                                        },
    'cirros-0.3.1-x86_64-uec': {'architecture': 'x86_64',
                                'os_type': 'linux',
                                'os_distro': 'cirros',
                                'os_version': '0.3.1'
                                },
    'cirros-0.3.2-x86_64-uec': {'architecture': 'x86_64',
                                'os_type': 'linux',
                                'os_distro': 'cirros',
                                'os_version': '0.3.2'
                                },
    'rhel-6.5-test-image': {'architecture': 'x86_64',
                            'os_type': 'linux',
                            'os_distro': 'rhel',
                            'os_version': '6.5'
                            }
}

SESSION = None

IMAGES = {}


def get_images():
    global IMAGES

    if IMAGES:
        return IMAGES

    if SESSION is not None and client_available:
        try:
            client = glanceclient.client.Client("2", session=SESSION)
        except Exception as e:
            # Handles any exception coming from openstack
            log.warn(_('Choosing predefined images since received '
                       'Openstack Exception: %s') % str(e))
        else:
            for image in client.images.list():
                image_id = image.id.encode('ascii', 'ignore')
                metadata = ["architecture", "type", "distribution", "version",
                            "os_distro", "os_type", "os_version"]
                if any(key in image.keys() for key in metadata):
                    IMAGES[image_id] = {}
                    for key in metadata:
                        if key in image.keys():
                            IMAGES[image_id][key] = image[key]

    if not IMAGES:
        IMAGES = PREDEF_IMAGES

    return IMAGES

#
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

import json
import logging
import requests

from toscaparser.utils.gettextutils import _
import translator.common.utils
from translator.hot.syntax.hot_resource import HotResource

log = logging.getLogger('heat-translator')


# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaCompute'

# A design issue to be resolved is how to translate the generic TOSCA server
# properties to OpenStack flavors and images.  At the Atlanta design summit,
# there was discussion on using Glance to store metadata and Graffiti to
# describe artifacts.  We will follow these projects to see if they can be
# leveraged for this TOSCA translation.
# For development purpose at this time, we temporarily hardcode a list of
# flavors and images here
FLAVORS = {'m1.xlarge': {'mem_size': 16384, 'disk_size': 160, 'num_cpus': 8},
           'm1.large': {'mem_size': 8192, 'disk_size': 80, 'num_cpus': 4},
           'm1.medium': {'mem_size': 4096, 'disk_size': 40, 'num_cpus': 2},
           'm1.small': {'mem_size': 2048, 'disk_size': 20, 'num_cpus': 1},
           'm1.tiny': {'mem_size': 512, 'disk_size': 1, 'num_cpus': 1},
           'm1.micro': {'mem_size': 128, 'disk_size': 0, 'num_cpus': 1},
           'm1.nano': {'mem_size': 64, 'disk_size': 0, 'num_cpus': 1}}

IMAGES = {'ubuntu-software-config-os-init': {'architecture': 'x86_64',
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
                                  'version': '6.5'}}


class ToscaCompute(HotResource):
    '''Translate TOSCA node type tosca.nodes.Compute.'''

    COMPUTE_HOST_PROP = (DISK_SIZE, MEM_SIZE, NUM_CPUS) = \
                        ('disk_size', 'mem_size', 'num_cpus')

    COMPUTE_OS_PROP = (ARCHITECTURE, DISTRIBUTION, TYPE, VERSION) = \
                      ('architecture', 'distribution', 'type', 'version')
    toscatype = 'tosca.nodes.Compute'

    def __init__(self, nodetemplate):
        super(ToscaCompute, self).__init__(nodetemplate,
                                           type='OS::Nova::Server')
        # List with associated hot port resources with this server
        self.assoc_port_resources = []
        pass

    def handle_properties(self):
        self.properties = self.translate_compute_flavor_and_image(
            self.nodetemplate.get_capability('host'),
            self.nodetemplate.get_capability('os'))
        self.properties['user_data_format'] = 'SOFTWARE_CONFIG'
        tosca_props = self.get_tosca_props()
        for key, value in tosca_props.items():
            self.properties[key] = value

    # To be reorganized later based on new development in Glance and Graffiti
    def translate_compute_flavor_and_image(self,
                                           host_capability,
                                           os_capability):
        hot_properties = {}
        host_cap_props = {}
        os_cap_props = {}
        image = None
        flavor = None
        if host_capability:
            for prop in host_capability.get_properties_objects():
                host_cap_props[prop.name] = prop.value
            # if HOST properties are not specified, we should not attempt to
            # find best match of flavor
            if host_cap_props:
                flavor = self._best_flavor(host_cap_props)
        if os_capability:
            for prop in os_capability.get_properties_objects():
                os_cap_props[prop.name] = prop.value
            # if OS properties are not specified, we should not attempt to
            # find best match of image
            if os_cap_props:
                image = self._best_image(os_cap_props)
        hot_properties['flavor'] = flavor
        hot_properties['image'] = image
        return hot_properties

    def _create_nova_flavor_dict(self):
        '''Populates and returns the flavors dict using Nova ReST API'''
        try:
            access_dict = translator.common.utils.get_ks_access_dict()
            access_token = translator.common.utils.get_token_id(access_dict)
            if access_token is None:
                return None
            nova_url = translator.common.utils.get_url_for(access_dict,
                                                           'compute')
            if not nova_url:
                return None
            nova_response = requests.get(nova_url + '/flavors/detail',
                                         headers={'X-Auth-Token':
                                                  access_token})
            if nova_response.status_code != 200:
                return None
            flavors = json.loads(nova_response.content)['flavors']
            flavor_dict = dict()
            for flavor in flavors:
                flavor_name = str(flavor['name'])
                flavor_dict[flavor_name] = {
                    'mem_size': flavor['ram'],
                    'disk_size': flavor['disk'],
                    'num_cpus': flavor['vcpus'],
                }
        except Exception as e:
            # Handles any exception coming from openstack
            log.warn(_('Choosing predefined flavors since received '
                       'Openstack Exception: %s') % str(e))
            return None
        return flavor_dict

    def _populate_image_dict(self):
        '''Populates and returns the images dict using Glance ReST API'''
        images_dict = {}
        try:
            access_dict = translator.common.utils.get_ks_access_dict()
            access_token = translator.common.utils.get_token_id(access_dict)
            if access_token is None:
                return None
            glance_url = translator.common.utils.get_url_for(access_dict,
                                                             'image')
            if not glance_url:
                return None
            glance_response = requests.get(glance_url + '/v2/images',
                                           headers={'X-Auth-Token':
                                                    access_token})
            if glance_response.status_code != 200:
                return None
            images = json.loads(glance_response.content)["images"]
            for image in images:
                image_resp = requests.get(glance_url + '/v2/images/' +
                                          image["id"],
                                          headers={'X-Auth-Token':
                                                   access_token})
                if image_resp.status_code != 200:
                    continue
                metadata = ["architecture", "type", "distribution", "version"]
                image_data = json.loads(image_resp.content)
                if any(key in image_data.keys() for key in metadata):
                    images_dict[image_data["name"]] = dict()
                    for key in metadata:
                        if key in image_data.keys():
                            images_dict[image_data["name"]][key] = \
                                image_data[key]
                else:
                    continue

        except Exception as e:
            # Handles any exception coming from openstack
            log.warn(_('Choosing predefined flavors since received '
                       'Openstack Exception: %s') % str(e))
        return images_dict

    def _best_flavor(self, properties):
        log.info(_('Choosing the best flavor for given attributes.'))
        # Check whether user exported all required environment variables.
        flavors = FLAVORS
        if translator.common.utils.check_for_env_variables():
            resp = self._create_nova_flavor_dict()
            if resp:
                flavors = resp

        # start with all flavors
        match_all = flavors.keys()

        # TODO(anyone): Handle the case where the value contains something like
        # get_input instead of a value.
        # flavors that fit the CPU count
        cpu = properties.get(self.NUM_CPUS)
        if cpu is None:
            self._log_compute_msg(self.NUM_CPUS, 'flavor')
        match_cpu = self._match_flavors(match_all, flavors, self.NUM_CPUS, cpu)

        # flavors that fit the mem size
        mem = properties.get(self.MEM_SIZE)
        if mem:
            mem = translator.common.utils.MemoryUnit.convert_unit_size_to_num(
                mem, 'MB')
        else:
            self._log_compute_msg(self.MEM_SIZE, 'flavor')
        match_cpu_mem = self._match_flavors(match_cpu, flavors,
                                            self.MEM_SIZE, mem)
        # flavors that fit the disk size
        disk = properties.get(self.DISK_SIZE)
        if disk:
            disk = translator.common.utils.MemoryUnit.\
                convert_unit_size_to_num(disk, 'GB')
        else:
            self._log_compute_msg(self.DISK_SIZE, 'flavor')
        match_cpu_mem_disk = self._match_flavors(match_cpu_mem, flavors,
                                                 self.DISK_SIZE, disk)
        # if multiple match, pick the flavor with the least memory
        # the selection can be based on other heuristic, e.g. pick one with the
        # least total resource
        if len(match_cpu_mem_disk) > 1:
            return self._least_flavor(match_cpu_mem_disk, flavors, 'mem_size')
        elif len(match_cpu_mem_disk) == 1:
            return match_cpu_mem_disk[0]
        else:
            return None

    def _best_image(self, properties):
        # Check whether user exported all required environment variables.
        images = IMAGES
        if translator.common.utils.check_for_env_variables():
            resp = self._populate_image_dict()
            if len(resp.keys()) > 0:
                images = resp
        match_all = images.keys()
        architecture = properties.get(self.ARCHITECTURE)
        if architecture is None:
            self._log_compute_msg(self.ARCHITECTURE, 'image')
        match_arch = self._match_images(match_all, images,
                                        self.ARCHITECTURE, architecture)
        type = properties.get(self.TYPE)
        if type is None:
            self._log_compute_msg(self.TYPE, 'image')
        match_type = self._match_images(match_arch, images, self.TYPE, type)
        distribution = properties.get(self.DISTRIBUTION)
        if distribution is None:
            self._log_compute_msg(self.DISTRIBUTION, 'image')
        match_distribution = self._match_images(match_type, images,
                                                self.DISTRIBUTION,
                                                distribution)
        version = properties.get(self.VERSION)
        if version is None:
            self._log_compute_msg(self.VERSION, 'image')
        match_version = self._match_images(match_distribution, images,
                                           self.VERSION, version)

        if len(match_version):
            return list(match_version)[0]

    def _match_flavors(self, this_list, this_dict, attr, size):
        '''Return from this list all flavors matching the attribute size.'''
        if not size:
            return list(this_list)
        matching_flavors = []
        for flavor in this_list:
            if isinstance(size, int):
                if this_dict[flavor][attr] >= size:
                    matching_flavors.append(flavor)
        log.debug(_('Returning list of flavors matching the attribute size.'))
        return matching_flavors

    def _least_flavor(self, this_list, this_dict, attr):
        '''Return from this list the flavor with the smallest attr.'''
        least_flavor = this_list[0]
        for flavor in this_list:
            if this_dict[flavor][attr] < this_dict[least_flavor][attr]:
                least_flavor = flavor
        return least_flavor

    def _match_images(self, this_list, this_dict, attr, prop):
        if not prop:
            return this_list
        matching_images = []
        for image in this_list:
            if this_dict[image][attr].lower() == str(prop).lower():
                matching_images.append(image)
        return matching_images

    def get_hot_attribute(self, attribute, args):
        attr = {}
        # Convert from a TOSCA attribute for a nodetemplate to a HOT
        # attribute for the matching resource.  Unless there is additional
        # runtime support, this should be a one to one mapping.

        # Note: We treat private and public IP  addresses equally, but
        # this will change in the future when TOSCA starts to support
        # multiple private/public IP addresses.
        log.debug(_('Converting TOSCA attribute for a nodetemplate to a HOT \
                  attriute.'))
        if attribute == 'private_address' or \
           attribute == 'public_address':
                attr['get_attr'] = [self.name, 'networks', 'private', 0]

        return attr

    def _log_compute_msg(self, prop, what):
        msg = _('No value is provided for Compute capability '
                'property "%(prop)s". This may set an undesired "%(what)s" '
                'in the template.') % {'prop': prop, 'what': what}
        log.warn(msg)

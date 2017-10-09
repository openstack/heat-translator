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

import logging

from toscaparser.utils.gettextutils import _
from translator.common import flavors as nova_flavors
from translator.common import images as glance_images
import translator.common.utils
from translator.hot.syntax.hot_resource import HotResource


log = logging.getLogger('heat-translator')


# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaCompute'


class ToscaCompute(HotResource):
    """Translate TOSCA node type tosca.nodes.Compute."""

    COMPUTE_HOST_PROP = (DISK_SIZE, MEM_SIZE, NUM_CPUS) = \
                        ('disk_size', 'mem_size', 'num_cpus')

    COMPUTE_OS_PROP = (ARCHITECTURE, DISTRIBUTION, TYPE, VERSION) = \
                      ('architecture', 'distribution', 'type', 'version')

    IMAGE_OS_PROP = (OS_DISTRO, OS_TYPE, OS_VERSION) = \
                    ('os_distro', 'os_type', 'os_version')
    toscatype = 'tosca.nodes.Compute'

    ALLOWED_NOVA_SERVER_PROPS = \
        ('admin_pass', 'availability_zone', 'block_device_mapping',
         'block_device_mapping_v2', 'config_drive', 'diskConfig', 'flavor',
         'flavor_update_policy', 'image', 'image_update_policy', 'key_name',
         'metadata', 'name', 'networks', 'personality', 'reservation_id',
         'scheduler_hints', 'security_groups', 'software_config_transport',
         'user_data', 'user_data_format', 'user_data_update_policy')

    def __init__(self, nodetemplate, csar_dir=None):
        super(ToscaCompute, self).__init__(nodetemplate,
                                           type='OS::Nova::Server',
                                           csar_dir=csar_dir)
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
            if key in self.ALLOWED_NOVA_SERVER_PROPS:
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
        if image:
            hot_properties['image'] = image
        else:
            hot_properties.pop('image', None)
        return hot_properties

    def _best_flavor(self, properties):
        log.info(_('Choosing the best flavor for given attributes.'))
        # Check whether user exported all required environment variables.
        flavors = nova_flavors.get_flavors()

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
        if 'image' in properties:
            return properties['image']

        # Check whether user exported all required environment variables.
        images = glance_images.get_images()
        match_all = images.keys()

        architecture = properties.get(self.ARCHITECTURE)
        if architecture is None:
            self._log_compute_msg(self.ARCHITECTURE, 'image')
        match_arch = self._match_images(match_all, images,
                                        [self.ARCHITECTURE], architecture)

        image_type = properties.get(self.TYPE)
        if image_type is None:
            self._log_compute_msg(self.TYPE, 'image')
        match_type = self._match_images(match_arch, images, [self.TYPE,
                                                             self.OS_TYPE],
                                        image_type)

        distribution = properties.get(self.DISTRIBUTION)
        if distribution is None:
            self._log_compute_msg(self.DISTRIBUTION, 'image')
        match_distribution = self._match_images(match_type, images,
                                                [self.DISTRIBUTION,
                                                 self.OS_DISTRO],
                                                distribution)

        version = properties.get(self.VERSION)
        if version is None:
            self._log_compute_msg(self.VERSION, 'image')
        match_version = self._match_images(match_distribution, images,
                                           [self.VERSION, self.OS_VERSION],
                                           version)

        if len(match_version):
            return list(match_version)[0]

    @staticmethod
    def _match_flavors(this_list, this_dict, attr, size):
        """Return from this list all flavors matching the attribute size."""
        if not size:
            return list(this_list)
        matching_flavors = []
        for flavor in this_list:
            if isinstance(size, int):
                if this_dict[flavor][attr] >= size:
                    matching_flavors.append(flavor)
        log.debug(_('Returning list of flavors matching the attribute size.'))
        return matching_flavors

    @staticmethod
    def _least_flavor(this_list, this_dict, attr):
        """Return from this list the flavor with the smallest attr."""
        least_flavor = this_list[0]
        for flavor in this_list:
            if this_dict[flavor][attr] < this_dict[least_flavor][attr]:
                least_flavor = flavor
        return least_flavor

    @staticmethod
    def _match_images(this_list, this_dict, attr_list, prop):
        if not prop:
            return this_list
        matching_images = []
        for image in this_list:
            for attr in attr_list:
                if attr in this_dict[image]:
                    if this_dict[image][attr].lower() == str(prop).lower():
                        matching_images.insert(0, image)
                else:
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

    @staticmethod
    def _log_compute_msg(prop, what):
        msg = _('No value is provided for Compute capability '
                'property "%(prop)s". This may set an undesired "%(what)s" '
                'in the template.') % {'prop': prop, 'what': what}
        log.warning(msg)

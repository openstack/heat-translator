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
import yaml

from translator.common.utils import MemoryUnit
from translator.hot.syntax.hot_resource import HotResource
log = logging.getLogger('heat-translator')


# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaNfvVduCompute'
TOSCA_ATTACHES_TO = 'tosca.relationships.nfv.AttachesTo'
depends_on_set = (
    TOSCA_ATTACHES_TO,
)


class ToscaNfvVduCompute(HotResource):
    """Translate TOSCA node type tosca.nodes.nfv.Vdu.Compute."""

    toscatype = 'tosca.nodes.nfv.Vdu.Compute'
    IMAGE = '#ADD_YOUR_IMAGE_HERE'
    FLAVOR_SUFFIX = '_flavor'

    def __init__(self, nodetemplate, csar_dir=None):
        super(ToscaNfvVduCompute, self).__init__(
            nodetemplate,
            type='OS::Nova::Server',
            csar_dir=csar_dir)
        # Associated resources
        self.assoc_port_resources = []
        self.virtual_storages = []
        self.flavor_resource_name = None

    def handle_properties(self):
        tosca_props = self.get_tosca_props()
        own_props = {}

        own_props['flavor'] = '{ get_resource: %s%s }' % (
            self.name,
            self.FLAVOR_SUFFIX,
        )

        for key, value in tosca_props.items():
            if key == 'name':
                own_props['name'] = value
            elif key == 'sw_image_data':
                # Users have to add an image ID or name because heat deprecated
                # creating an image from a local file.
                own_props['image'] = '%s' % (
                    self.IMAGE
                )

        # Multi virtual_storages support
        requirements = self.nodetemplate.requirements
        self.virtual_storages = []
        for req in requirements:
            vs_val = req.get('virtual_storage')
            if isinstance(vs_val, dict):
                if vs_val.get('node') is not None:
                    self.virtual_storages.append(vs_val['node'])
            else:
                self.virtual_storages.append(vs_val)
        dict_rsrcs = self.nodetemplate.templates
        bdmv2s = []
        for vs_name in self.virtual_storages:
            # Supported virtual storage types:
            # - tosca.nodes.nfv.Vdu.VirtualBlockStorage
            vs_type = None
            for rsrc_name, rsrc_info in dict_rsrcs.items():
                rsrc_type = rsrc_info['type']
                if rsrc_type == 'tosca.nodes.nfv.Vdu.VirtualBlockStorage':
                    vs_type = rsrc_type

            if vs_type is not None:
                bdmv2s.append({
                    'volume_id': '{ get_resource: %s }' % (vs_name)
                })
            else:
                log.warning(('Unsupported virtual_storage, '
                             'vdu_name:%s, virtual_storage_name:%s')
                            % (self.name, vs_name))

        if bdmv2s != []:
            own_props['block_device_mapping_v2'] = bdmv2s

        self.flavor_resource_name = self.name + self.FLAVOR_SUFFIX

        # Remove depends_on
        self.remove_depends_on(depends_on_set)

        self.properties = own_props

    def handle_expansion(self):
        hot_resources = []
        flavor_props = {}

        tosca_capas = self.nodetemplate.get_capability('virtual_compute')
        tosca_c_props = tosca_capas.get_properties_objects()

        for prop in tosca_c_props:
            if prop.name == 'virtual_cpu':
                flavor_props['vcpus'] = prop.value['num_virtual_cpu']
            elif prop.name == 'virtual_memory':
                # Convert to MiB
                flavor_props['ram'] = \
                    MemoryUnit.convert_unit_size_to_num(
                        prop.value['virtual_mem_size'], 'MiB')
            elif prop.name == 'virtual_local_storage':
                # Convert to GiB
                flavor_props['disk'] = \
                    MemoryUnit.convert_unit_size_to_num(
                        prop.value[0]['size_of_storage'], 'GiB')
            elif prop.name == 'compute_requirements':
                if prop.value.get('nova_extra_specs') is not None:
                    nova_es = prop.value['nova_extra_specs']
                    try:
                        # Check if it is in yaml format
                        yaml.safe_load(nova_es)
                        flavor_props['extra_specs'] = nova_es
                    except Exception:
                        log.warning(('Unsupported format of '
                                     'compute_requirements, '
                                     'vdu_name:%s, nova_extra_specs:%s')
                                    % (self.name, nova_es))

        hot_resources.append(
            HotResource(
                self.nodetemplate,
                type='OS::Nova::Flavor',
                name=self.flavor_resource_name,
                properties=flavor_props,
            )
        )

        return hot_resources

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

from translator.common.utils import MemoryUnit
from translator.hot.syntax.hot_resource import HotResource


# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaNfvVduVirtualBlockStorage'


class ToscaNfvVduVirtualBlockStorage(HotResource):
    """Translate TOSCA node type tosca.nodes.nfv.Vdu.VirtualBlockStorage."""

    toscatype = 'tosca.nodes.nfv.Vdu.VirtualBlockStorage'
    IMAGE = '#ADD_YOUR_IMAGE_HERE'

    def __init__(self, nodetemplate, csar_dir=None):
        super(ToscaNfvVduVirtualBlockStorage, self).__init__(
            nodetemplate,
            type='OS::Cinder::Volume',
            csar_dir=csar_dir)

    def handle_properties(self):
        tosca_props = self.get_tosca_props()
        own_props = {}

        for key, value in tosca_props.items():
            # This image's value is replaced after translation.
            if key == 'sw_image_data':
                # Users have to add an image ID or name because heat deprecated
                # creating an image from a local file.
                own_props['image'] = '%s' % (
                    self.IMAGE
                )
            elif key == 'virtual_block_storage_data':
                # Convert to GiB
                own_props['size'] = \
                    MemoryUnit.convert_unit_size_to_num(
                        value['size_of_storage'], 'GiB')

        self.properties = own_props

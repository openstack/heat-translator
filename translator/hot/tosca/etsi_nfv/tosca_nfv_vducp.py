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

from translator.hot.syntax.hot_resource import HotResource
log = logging.getLogger('heat-translator')


# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaNfvVducp'
TOSCA_LINKS_TO = 'tosca.relationships.nfv.VirtualLinksTo'
TOSCA_BINDS_TO = 'tosca.relationships.nfv.VirtualBindsTo'
depends_on_set = (
    TOSCA_LINKS_TO,
    TOSCA_BINDS_TO,
)


class ToscaNfvVducp(HotResource):
    """Translate TOSCA node type tosca.nodes.nfv.VduCp."""

    toscatype = 'tosca.nodes.nfv.VduCp'
    EXTERNAL_VL = '#ADD_YOUR_NETWORK_HERE'

    def __init__(self, nodetemplate, csar_dir=None):
        super(ToscaNfvVducp, self).__init__(
            nodetemplate,
            type='OS::Neutron::Port',
            csar_dir=csar_dir)

        # Default order
        self.order = 0

        # Extract virtual_link and virtual_binding
        self.virtual_link = None
        self.virtual_binding = None
        requirements = self.nodetemplate.requirements
        for req in requirements:
            if 'virtual_link' in req:
                vl_val = req.get('virtual_link')
                if isinstance(vl_val, dict):
                    self.virtual_link = vl_val.get('node')
                else:
                    self.virtual_link = vl_val
            elif 'virtual_binding' in req:
                self.virtual_binding = req.get('virtual_binding')

    def _generate_networks_for_compute(self, port_resources):
        '''Generate compute networks property list from the port resources.'''
        networks = []
        for resource in port_resources:
            networks.append({'port': '{ get_resource: %s }' % (resource.name)})
        return networks

    def _insert_sorted_resource(self, resources, resource):
        '''Insert a resource in the list of resources and keep the order.'''
        lo = 0
        hi = len(resources)
        while lo < hi:
            mid = (lo + hi) // 2
            if resource.order < resources[mid].order:
                hi = mid
            else:
                lo = mid + 1
        resources.insert(lo, resource)

    def handle_properties(self):
        tosca_props = self.get_tosca_props()
        own_props = {}

        if self.virtual_link:
            own_props['network'] = '{ get_resource: %s }' % (
                self.virtual_link
            )
        else:
            # If no virtual_binding is specified in VNFD, users
            # have to input external VL given in instantiation VNF request.
            own_props['network'] = '%s' % (
                self.EXTERNAL_VL
            )

        for key, value in tosca_props.items():
            if key == 'order':
                self.order = value
            elif key == 'vnic_type':
                own_props['binding:vnic_type'] = value

        # Remove depends_on
        self.remove_depends_on(depends_on_set)

        binds_to = None
        for rel, node in self.nodetemplate.relationships.items():
            # Check for BindsTo relationship. If found add network to the
            # network property of the corresponding compute resource
            if not binds_to and rel.is_derived_from(TOSCA_BINDS_TO):
                binds_to = node
                for hot_resource in self.depends_on_nodes:
                    if binds_to.name == hot_resource.name:
                        port_rsrcs = hot_resource.assoc_port_resources
                        self._insert_sorted_resource(port_rsrcs, self)
                        networks = \
                            self._generate_networks_for_compute(port_rsrcs)
                        hot_resource.properties['networks'] = networks
                        break

        self.properties = own_props

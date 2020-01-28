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

from translator.common.utils import MemoryUnit
from translator.hot.syntax.hot_resource import HotResource

log = logging.getLogger('heat-translator')


# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaNfvVnfVirtualLink'


class ToscaNfvVnfVirtualLink(HotResource):
    """Translate TOSCA node type tosca.nodes.nfv.VnfVirtualLink."""

    toscatype = 'tosca.nodes.nfv.VnfVirtualLink'
    SUBNET_SUFFIX = '_subnet'
    QOSPOLICY_SUFFIX = '_qospolicy'
    BANDWIDTH_SUFFIX = '_bandwidth'
    ip_map = {
        'ipv4': '4',
        'ipv6': '6',
    }

    def __init__(self, nodetemplate, csar_dir=None):

        # Check if it is an IP network
        tosca_props = {}
        for prop in nodetemplate.get_properties_objects():
            tosca_props[prop.name] = prop.value

        lp = tosca_props.get('connectivity_type').get('layer_protocols')
        self.ip_protocol = list(set(self.ip_map.keys()) & set(lp))

        # Branch by IP or not
        if self.ip_protocol:
            super(ToscaNfvVnfVirtualLink, self).__init__(
                nodetemplate,
                type='OS::Neutron::Net',
                csar_dir=csar_dir
            )
        else:
            super(ToscaNfvVnfVirtualLink, self).__init__(
                nodetemplate,
                csar_dir=csar_dir
            )
            log.warning(('Unsupported layer_protocols, '
                         'virtual_link_name:%s, protocol_name:%s')
                        % (self.name, lp))

    def handle_properties(self):

        # Branch by IP or not
        if self.ip_protocol:
            tosca_props = self.get_tosca_props()
            own_props = {}

            self.is_leaf = False
            for key, value in tosca_props.items():
                if key == 'vl_profile':
                    mbr = value['max_bitrate_requirements']
                    if 'leaf' in mbr:
                        max_bps = mbr['leaf']
                        # Convert to KiB
                        self.max_kbps = \
                            max_bps / MemoryUnit.UNIT_SIZE_DICT['KiB']
                        self.is_leaf = True
                    else:
                        log.warning('Can not set the required properties '
                                    'max_kbps on HOT.'
                                    'virtual_link_name:%s' % self.name)

            if self.is_leaf:
                own_props['qos_policy'] = '{ get_resource: %s%s }' % (
                    self.name,
                    self.QOSPOLICY_SUFFIX,
                )

            self.properties = own_props

        else:
            pass

    def handle_expansion(self):
        hot_resources = []

        # Branch by IP or not
        if self.ip_protocol:
            tosca_props = self.get_tosca_props()

            # subnet props
            subnet_props = {}
            subnet_props['ip_version'] = self.ip_map.get(self.ip_protocol[0])
            subnet_props['network'] = '{ get_resource: %s }' % (self.name)

            for key, value in tosca_props.items():
                if key == 'vl_profile':
                    if 'virtual_link_protocol_data' in value:
                        vlpd = value['virtual_link_protocol_data']
                        if 'l3_protocol_data' in vlpd[0]:
                            l3pd = vlpd[0]['l3_protocol_data']
                            subnet_props['cidr'] = l3pd['cidr']

            subnet_resource_name = self.name + self.SUBNET_SUFFIX

            hot_resources.append(
                HotResource(
                    self.nodetemplate,
                    type='OS::Neutron::Subnet',
                    name=subnet_resource_name,
                    properties=subnet_props,
                )
            )

            # qospolicy_props props
            qospolicy_props = {}

            qospolicy_resource_name = self.name + self.QOSPOLICY_SUFFIX

            # bandwidth props
            bandwidth_props = {}
            bandwidth_props['policy'] = '{ get_resource: %s%s }' % (
                self.name,
                self.QOSPOLICY_SUFFIX,
            )

            bandwidth_resource_name = self.name + self.BANDWIDTH_SUFFIX

            # Create QoSPolicy and QoSBandwidthLimitRule resources
            # only when max_bitrate_requirements has leaf property.
            if self.is_leaf:
                hot_resources.append(
                    HotResource(
                        self.nodetemplate,
                        type='OS::Neutron::QoSPolicy',
                        name=qospolicy_resource_name,
                        properties=qospolicy_props,
                    )
                )

                bandwidth_props['max_kbps'] = self.max_kbps
                hot_resources.append(
                    HotResource(
                        self.nodetemplate,
                        type='OS::Neutron::QoSBandwidthLimitRule',
                        name=bandwidth_resource_name,
                        properties=bandwidth_props,
                    )
                )

        else:
            pass

        return hot_resources

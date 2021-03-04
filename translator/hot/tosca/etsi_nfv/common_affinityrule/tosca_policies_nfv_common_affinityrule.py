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

from translator.hot.syntax.hot_resource import HotResource

# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaNfvCommonAffinityRule'


class ToscaNfvCommonAffinityRule(HotResource):
    """Translate common TOSCA policy type tosca.policies.nfv.AffinityRule."""

    GROUP_SUFFIX = '_group'

    def __init__(self, policy, csar_dir=None, hot_template_parameters=None):
        self.own_resource_name = policy.name + self.GROUP_SUFFIX
        super(ToscaNfvCommonAffinityRule, self).__init__(
            policy,
            name=self.own_resource_name,
            type='OS::Nova::ServerGroup',
            csar_dir=csar_dir)
        self.policy = policy
        self.hot_template_parameters = hot_template_parameters

    def handle_properties(self, resources):
        policy_props = self.policy.properties
        rule = 'anti-affinity' if self.is_anti else 'affinity'

        # NOTE: In ETSI-NFV SOL001, nfvi_node/zone/zone_group/nfvi_pop
        # is specified as 'scope'.
        # This code only supports nfvi_node as 'scope'and no conversion
        # for other'scope'.
        scope = policy_props.get('scope', None)
        if scope != 'nfvi_node':
            self.name = None
            self.type = None
            return

        # NOTE: In ETSI-NFV SOL001,
        # - tosca.nodes.nfv.Vdu.Compute
        # - tosca.nodes.nfv.VnfVirtualLink
        # - tosca.groups.nfv.PlacementGroup
        # is specified as'targets'.
        # This code only supports tosca.nodes.nfv.Vdu.Compute as 'targets'
        # and no conversion for other 'targets'.
        is_exists_server = False
        for resource in resources:
            if self.policy.type in self.toscatype and \
                    resource.name in self.policy.targets and \
                    resource.type == 'OS::Nova::Server':
                self.properties['name'] = self.name
                self.properties['policies'] = [rule]
                if not resource.properties.get('scheduler_hints'):
                    resource.properties['scheduler_hints'] = {}
                resource.properties['scheduler_hints'].update(
                    {'group': '{ get_resource: %s }' % (self.name)}
                )
                is_exists_server = True

        if is_exists_server is False:
            self.name = None
            self.type = None

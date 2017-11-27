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

from collections import defaultdict

from translator.hot.syntax.hot_resource import HotResource
# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaClusterAutoscaling'

SCALE_POLICY = 'senlin.policy.scaling-1.0'
SERVER_TYPE = 'os.nova.server-1.0'
SCALE_TYPE = {'SCALE_IN': 'CLUSTER_SCALE_IN',
              'SCALE_OUT': 'CLUSTER_SCALE_OUT'}

ALARM_METER_NAME = {'utilization': 'cpu_util'}
ALARM_COMPARISON_OPERATOR = {'greater_than': 'gt', 'gerater_equal': 'ge',
                             'less_than': 'lt', 'less_equal': 'le',
                             'equal': 'eq', 'not_equal': 'ne'}
ALARM_STATISTIC = {'mean': 'mean', 'median': 'median', 'summary': 'sum',
                   'maximum': 'max', 'minimum': 'min', 'last': 'last',
                   'std': 'std', 'first': 'first', 'count': 'count'}


class ToscaClusterAutoscaling(HotResource):
    '''Translate TOSCA node type tosca.policies.Scaling.Cluster'''

    toscatype = 'tosca.policies.Scaling.Cluster'

    def __init__(self, policy, csar_dir=None):
        hot_type = "OS::Senlin::Policy"
        super(ToscaClusterAutoscaling, self).__init__(policy,
                                                      type=hot_type,
                                                      csar_dir=csar_dir)
        self.policy = policy

    def _generate_scale_properties(self,
                                   target_cluster_nodes,
                                   cluster_scale_type):
        properties = {}
        bindings = []
        policy_res = {}
        adjustment = {}
        properties["type"] = SCALE_POLICY
        for cluster_node in target_cluster_nodes:
            bindings.append({'cluster': cluster_node})
        properties["bindings"] = bindings
        policy_res["event"] = cluster_scale_type
        adjustment["type"] = "CHANGE_IN_CAPACITY"
        adjustment["number"] = self.\
            policy.entity_tpl["properties"]["increment"]
        policy_res["adjustment"] = adjustment
        properties["properties"] = policy_res
        return properties

    def handle_expansion(self):
        hot_resources = []
        hot_type = 'OS::Aodh::GnocchiAggregationByResourcesAlarm'
        trigger_receivers = defaultdict(list)
        for node in self.policy.targets:
            for trigger in self.policy.entity_tpl['triggers']:
                for action in self.policy.\
                    entity_tpl['triggers'][trigger]['action']:
                    scale_name = action
                    action_sample = self.policy.\
                        entity_tpl['triggers'][trigger]['action'][action]
                    scale_type = action_sample['type']
                    scale_implement = action_sample['implementation']
                (entity, method) = scale_implement.split('.')
                receiver_prop = {}
                receiver_prop['cluster'] = {
                    "get_resource": "%s_cluster" % node
                    }
                receiver_prop['action'] = SCALE_TYPE[scale_type]
                receiver_prop['type'] = method
                receiver_name = node + '_' + scale_name + '_receiver'
                trigger_receivers[trigger].append(receiver_name)
                receiver_resources = HotResource(self.nodetemplate,
                                                 type='OS::Senlin::Receiver',
                                                 name=receiver_name,
                                                 properties=receiver_prop)
                hot_resources.append(receiver_resources)

        for trigger in self.policy.entity_tpl['triggers']:
            sample = self.policy.\
                entity_tpl['triggers'][trigger]['condition']
            (meter_name, comparison_operator, threshold) = \
                sample["constraint"].split()
            threshold = threshold.strip("%")
            alarm_prop = {}
            alarm_prop["description"] = self.policy.entity_tpl['description']
            alarm_prop["metric"] = self.policy.\
                entity_tpl['triggers'][trigger]['event_type']['metric']
            alarm_prop["aggregation_method"] = \
                ALARM_STATISTIC[sample['aggregation_method']]
            alarm_prop["granularity"] = sample["granularity"]
            alarm_prop["evaluation_periods"] = sample["evaluations"]
            alarm_prop["threshold"] = threshold
            alarm_prop["resource_type"] = sample.get("resource_type",
                                                     "instance")
            alarm_prop["comparison_operator"] = \
                ALARM_COMPARISON_OPERATOR[comparison_operator]
            alarm_prop["repeat_actions"] = "True"
            alarm_prop["alarm_actions"] = []
            for index in range(len(trigger_receivers[trigger])):
                alarm_prop["alarm_actions"].\
                    append({'get_attr': [trigger_receivers[trigger][index],
                                         'channel',
                                         'alarm_url']})
            ceilometer_resources = HotResource(self.nodetemplate,
                                               type=hot_type,
                                               name=trigger + '_alarm',
                                               properties=alarm_prop)
            hot_resources.append(ceilometer_resources)
        return hot_resources

    def handle_properties(self, resources):
        remove_resources = []
        networks = defaultdict(list)
        for index, resource in enumerate(resources):
            if resource.type == 'OS::Neutron::Port':
                for hot_resource in resource.depends_on_nodes:
                    if hot_resource.type != 'OS::Neutron::Net':
                        networks[hot_resource.name].\
                            append(
                            {'network': '%s' % resource.properties['network']}
                            )
                remove_resources.append(resource)
            elif resource.type == 'OS::Neutron::Net':
                remove_resources.append(resource)
            elif resource.name in self.policy.targets and \
                resource.type != 'OS::Senlin::Policy':
                props = {}
                del resource.properties['user_data_format']
                del resource.properties['networks']
                props['type'] = SERVER_TYPE
                props['properties'] = resource.properties
                profile_resources = \
                    HotResource(resource,
                                type='OS::Senlin::Profile',
                                name=resource.name,
                                properties=props)
                resources.pop(index)
                resources.insert(index, profile_resources)
        for remove_resource in remove_resources:
            resources.remove(remove_resource)

        for index, resource in enumerate(resources):
            if resource.name in self.policy.targets:
                resource.properties['properties']['networks'] = \
                    networks[resource.name]

        for node in self.policy.targets:
            props = {}
            props["profile"] = {'get_resource': '%s' % node}
            temp = self.policy.entity_tpl["properties"]
            props["min_size"] = temp["min_instances"]
            props["max_size"] = temp["max_instances"]
            props["desired_capacity"] = temp["default_instances"]
            self.cluster_name = '%s_cluster' % node
            cluster_resources = \
                HotResource(self.nodetemplate,
                            type='OS::Senlin::Cluster',
                            name=self.cluster_name,
                            properties=props)
            resources.append(cluster_resources)

        trigger_num = len(self.policy.entity_tpl['triggers'])
        for num, trigger in enumerate(self.policy.entity_tpl['triggers']):
            target_cluster_nodes = []
            for action in self.policy.\
                entity_tpl['triggers'][trigger]['action']:
                scale_type = self.policy.\
                    entity_tpl['triggers'][trigger]['action'][action]['type']
            for node in self.policy.targets:
                target_cluster_nodes.\
                    append({"get_resource": "%s_cluster" % node})
            cluster_scale_type = SCALE_TYPE[scale_type]
            scale_in_props = \
                self._generate_scale_properties(target_cluster_nodes,
                                                cluster_scale_type)
            if num == trigger_num - 1:
                self.name = self.name + '_' + trigger
                self.properties = scale_in_props
                break
            policy_resources = \
                HotResource(self.nodetemplate,
                            type='OS::Senlin::Policy',
                            name=self.name + '_' + trigger,
                            properties=scale_in_props)
            resources.append(policy_resources)
        return resources

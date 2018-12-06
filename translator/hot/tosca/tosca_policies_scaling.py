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


from collections import OrderedDict
import yaml

from translator.hot.syntax.hot_resource import HotResource
# Name used to dynamically load appropriate map class.
TARGET_CLASS_NAME = 'ToscaAutoscaling'
HEAT_TEMPLATE_BASE = """
heat_template_version: 2013-05-23
"""
ALARM_STATISTIC = {'mean': 'mean', 'median': 'median', 'summary': 'sum',
                   'maximum': 'max', 'minimum': 'min', 'last': 'last',
                   'std': 'std', 'first': 'first', 'count': 'count'}
SCALING_RESOURCES = ["OS::Heat::ScalingPolicy", "OS::Heat::AutoScalingGroup",
                     "OS::Aodh::GnocchiAggregationByResourcesAlarm",
                     "OS::Aodh::EventAlarm"]


class ToscaAutoscaling(HotResource):
    '''Translate TOSCA node type tosca.policies.Scaling'''

    toscatype = 'tosca.policies.Scaling'

    def __init__(self, policy, csar_dir=None, hot_template_parameters=None):
        hot_type = "OS::Heat::ScalingPolicy"
        super(ToscaAutoscaling, self).__init__(policy,
                                               type=hot_type,
                                               csar_dir=csar_dir)
        self.policy = policy
        self.hot_template_parameters = hot_template_parameters

    def handle_expansion(self):
        if self.policy.entity_tpl.get('triggers'):
            hot_type = 'OS::Aodh::GnocchiAggregationByResourcesAlarm'
            sample = self.policy.\
                entity_tpl["triggers"]["resize_compute"]["condition"]
            prop = {}
            prop["description"] = self.policy.entity_tpl.get('description')
            prop["metric"] = "cpu_util"
            if sample:
                prop["aggregation_method"] = \
                    ALARM_STATISTIC[sample["aggregation_method"]]
                prop["granularity"] = sample["granularity"]
                prop["threshold"] = sample["evaluations"]
                prop["resource_type"] = sample.get("resource_type", "instance")
            prop["comparison_operator"] = "gt"
            alarm_name = self.name.replace('_scale_in', '').\
                replace('_scale_out', '')
            ceilometer_resources = HotResource(self.nodetemplate,
                                               type=hot_type,
                                               name=alarm_name + '_alarm',
                                               properties=prop)
            hot_resources = [ceilometer_resources]
            return hot_resources

    def represent_ordereddict(self, dumper, data):
        nodes = []
        for key, value in data.items():
            node_key = dumper.represent_data(key)
            node_value = dumper.represent_data(value)
            nodes.append((node_key, node_value))
        return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', nodes)

    def _handle_nested_template(self, scale_res):
        template_dict = yaml.safe_load(HEAT_TEMPLATE_BASE)
        template_dict['description'] = 'Tacker Scaling template'
        if self.hot_template_parameters:
            all_params = OrderedDict()
            for parameter in self.hot_template_parameters:
                all_params.update(parameter.get_dict_output())
            template_dict.update({'parameters': all_params})

        template_dict["resources"] = {}
        dict_res = OrderedDict()
        for res in scale_res:
            dict_res = res.get_dict_output()
            res_name = list(dict_res.keys())[0]
            template_dict["resources"][res_name] = \
                dict_res[res_name]

        yaml.add_representer(OrderedDict, self.represent_ordereddict)
        yaml.add_representer(dict, self.represent_ordereddict)
        yaml_string = yaml.dump(template_dict, default_flow_style=False)
        yaml_string = yaml_string.replace('\'', '').replace('\n\n', '\n')
        self.nested_template = {
            self.policy.name + '_res.yaml': yaml_string
        }

    def handle_properties(self, resources):
        self.properties = {}
        self.properties["auto_scaling_group_id"] = {
            'get_resource': self.policy.name + '_group'
        }
        self.properties["adjustment_type"] = "change_in_capacity "
        self.properties["scaling_adjustment"] = self.\
            policy.entity_tpl["properties"]["increment"]
        self.properties["cooldown"] =\
            self.policy.entity_tpl["properties"]["cooldown"]
        delete_res_names = []
        scale_res = []
        for index, resource in enumerate(resources):
            if resource.name in self.policy.targets and \
                resource.type != 'OS::Heat::AutoScalingGroup':
                temp = self.policy.entity_tpl["properties"]
                props = {}
                res = {}
                res["min_size"] = temp["min_instances"]
                res["max_size"] = temp["max_instances"]
                res["desired_capacity"] = temp["default_instances"]
                res["cooldown"] = temp["cooldown"]
                props['type'] = resource.type
                props['properties'] = resource.properties
                res['resource'] = {'type': self.policy.name + '_res.yaml'}
                scaling_resources = \
                    HotResource(resource,
                                type='OS::Heat::AutoScalingGroup',
                                name=self.policy.name + '_group',
                                properties=res)

            if resource.type not in SCALING_RESOURCES:
                delete_res_names.append(resource.name)
                scale_res.append(resource)
        self._handle_nested_template(scale_res)
        resources = [tmp_res
                     for tmp_res in resources
                     if tmp_res.name not in delete_res_names]
        resources.append(scaling_resources)
        return resources

    def extract_substack_templates(self, base_filename, hot_template_version):
        return self.nested_template

    def embed_substack_templates(self, hot_template_version):
        pass

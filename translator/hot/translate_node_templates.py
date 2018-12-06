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

import copy
import importlib
import logging
import os
import six

from collections import OrderedDict
from toscaparser.functions import Concat
from toscaparser.functions import GetAttribute
from toscaparser.functions import GetInput
from toscaparser.functions import GetOperationOutput
from toscaparser.functions import GetProperty
from toscaparser.properties import Property
from toscaparser.relationship_template import RelationshipTemplate
from toscaparser.utils.gettextutils import _
from translator.common.exception import ToscaClassAttributeError
from translator.common.exception import ToscaClassImportError
from translator.common.exception import ToscaModImportError
from translator.common.exception import UnsupportedTypeError
from translator.common import utils
from translator.conf.config import ConfigProvider as translatorConfig
from translator.hot.syntax.hot_resource import HotResource
from translator.hot.tosca.tosca_block_storage_attachment import (
    ToscaBlockStorageAttachment
    )

###########################
# Module utility Functions
# for dynamic class loading
###########################


def _generate_type_map():
    '''Generate TOSCA translation types map.

    Load user defined classes from location path specified in conf file.
    Base classes are located within the tosca directory.

    '''

    # Base types directory
    BASE_PATH = 'translator/hot/tosca'

    # Custom types directory defined in conf file
    custom_path = translatorConfig.get_value('DEFAULT',
                                             'custom_types_location')

    # First need to load the parent module, for example 'contrib.hot',
    # for all of the dynamically loaded classes.
    classes = []
    _load_classes((BASE_PATH, custom_path), classes)
    try:
        types_map = {clazz.toscatype: clazz for clazz in classes}
    except AttributeError as e:
        raise ToscaClassAttributeError(message=e.message)

    return types_map


def _load_classes(locations, classes):
    '''Dynamically load all the classes from the given locations.'''

    for cls_path in locations:
        # Use the absolute path of the class path
        abs_path = os.path.dirname(os.path.abspath(__file__))
        abs_path = abs_path.replace('translator/hot', cls_path)

        # Grab all the tosca type module files in the given path
        mod_files = [f for f in os.listdir(abs_path) if f.endswith('.py') and
                     not f.startswith('__init__') and
                     f.startswith('tosca_')]

        # For each module, pick out the target translation class
        for f in mod_files:
            # NOTE: For some reason the existing code does not use the map to
            # instantiate ToscaBlockStorageAttachment. Don't add it to the map
            # here until the dependent code is fixed to use the map.
            if f == 'tosca_block_storage_attachment.py':
                continue

            mod_name = cls_path + '/' + f.strip('.py')
            mod_name = mod_name.replace('/', '.')
            try:
                mod = importlib.import_module(mod_name)
                target_name = getattr(mod, 'TARGET_CLASS_NAME')
                clazz = getattr(mod, target_name)
                classes.append(clazz)
            except ImportError:
                raise ToscaModImportError(mod_name=mod_name)
            except AttributeError:
                if target_name:
                    raise ToscaClassImportError(name=target_name,
                                                mod_name=mod_name)
                else:
                    # TARGET_CLASS_NAME is not defined in module.
                    # Re-raise the exception
                    raise

##################
# Module constants
##################

SECTIONS = (TYPE, PROPERTIES, REQUIREMENTS, INTERFACES, LIFECYCLE, INPUT) = \
           ('type', 'properties', 'requirements',
            'interfaces', 'lifecycle', 'input')

# TODO(anyone):  the following requirement names should not be hard-coded
# in the translator.  Since they are basically arbitrary names, we have to get
# them from TOSCA type definitions.
# To be fixed with the blueprint:
# https://blueprints.launchpad.net/heat-translator/+spec/tosca-custom-types
REQUIRES = (CONTAINER, DEPENDENCY, DATABASE_ENDPOINT, CONNECTION, HOST) = \
           ('container', 'dependency', 'database_endpoint',
            'connection', 'host')

INTERFACES_STATE = (CREATE, START, CONFIGURE, START, DELETE) = \
                   ('create', 'stop', 'configure', 'start', 'delete')


TOSCA_TO_HOT_REQUIRES = {'container': 'server', 'host': 'server',
                         'dependency': 'depends_on', "connects": 'depends_on'}

TOSCA_TO_HOT_PROPERTIES = {'properties': 'input'}
log = logging.getLogger('heat-translator')

TOSCA_TO_HOT_TYPE = _generate_type_map()

BASE_TYPES = six.string_types + six.integer_types + (dict, OrderedDict)

HOT_SCALING_POLICY_TYPE = ["OS::Heat::AutoScalingGroup",
                           "OS::Senlin::Profile"]


class TranslateNodeTemplates(object):
    '''Translate TOSCA NodeTemplates to Heat Resources.'''

    def __init__(self, tosca, hot_template, csar_dir=None):
        self.tosca = tosca
        self.nodetemplates = self.tosca.nodetemplates
        self.hot_template = hot_template
        self.csar_dir = csar_dir
        # list of all HOT resources generated
        self.hot_resources = []
        # mapping between TOSCA nodetemplate and HOT resource
        log.debug(_('Mapping between TOSCA nodetemplate and HOT resource.'))
        self.hot_lookup = {}
        self.policies = self.tosca.topology_template.policies
        # stores the last deploy of generated behavior for a resource
        # useful to satisfy underlying dependencies between interfaces
        self.last_deploy_map = {}
        self.hot_template_version = None
        self.processed_policy_res = []

    def translate(self):
        return self._translate_nodetemplates()

    def _recursive_handle_properties(self, resource):
        '''Recursively handle the properties of the depends_on_nodes nodes.'''
        # Use of hashtable (dict) here should be faster?
        if resource in self.processed_resources:
            return
        self.processed_resources.append(resource)
        for depend_on in resource.depends_on_nodes:
            self._recursive_handle_properties(depend_on)

        if resource.type == "OS::Nova::ServerGroup":
            resource.handle_properties(self.hot_resources)
        elif resource.type in ("OS::Heat::ScalingPolicy",
                               "OS::Senlin::Policy"):
            if resource.name in self.processed_policy_res:
                return
            self.processed_policy_res.append(resource.name)
            self.hot_resources = \
                resource.handle_properties(self.hot_resources)
            extra_hot_resources = []
            for res in self.hot_resources:
                if res.type == 'OS::Heat::ScalingPolicy':
                    extra_res = copy.deepcopy(res)
                    scaling_adjustment = res.properties['scaling_adjustment']
                    if scaling_adjustment < 0:
                        res.name = res.name + '_scale_in'
                        extra_res.name = extra_res.name + '_scale_out'
                        extra_res.properties['scaling_adjustment'] = \
                            -1 * scaling_adjustment
                        extra_hot_resources.append(extra_res)
                        self.processed_policy_res.append(res.name)
                        self.processed_policy_res.append(extra_res.name)
                    elif scaling_adjustment > 0:
                        res.name = res.name + '_scale_out'
                        extra_res.name = extra_res.name + '_scale_in'
                        extra_res.properties['scaling_adjustment'] = \
                            -1 * scaling_adjustment
                        extra_hot_resources.append(extra_res)
                        self.processed_policy_res.append(res.name)
                        self.processed_policy_res.append(extra_res.name)
                    else:
                        continue
            self.hot_resources += extra_hot_resources
        else:
            resource.handle_properties()

    def _translate_nodetemplates(self):
        log.debug(_('Translating the node templates.'))
        suffix = 0
        # Copy the TOSCA graph: nodetemplate
        for node in self.nodetemplates:
            base_type = HotResource.get_base_type_str(node.type_definition)
            if base_type not in TOSCA_TO_HOT_TYPE:
                raise UnsupportedTypeError(type=_('%s') % base_type)
            hot_node = TOSCA_TO_HOT_TYPE[base_type](node,
                                                    csar_dir=self.csar_dir)
            self.hot_resources.append(hot_node)
            self.hot_lookup[node] = hot_node

            # BlockStorage Attachment is a special case,
            # which doesn't match to Heat Resources 1 to 1.
            if base_type == "tosca.nodes.Compute":
                requirements = node.requirements
                if requirements:
                    # Find the name of associated BlockStorage node
                    for requires in requirements:
                        volume_name = None
                        for value in requires.values():
                            if isinstance(value, dict):
                                for node_name in value.values():
                                    for n in self.nodetemplates:
                                        if n.name == node_name and \
                                            n.is_derived_from(
                                                "tosca.nodes.BlockStorage"):
                                            volume_name = node_name
                                            break
                            else:
                                for n in self.nodetemplates:
                                    if n.name == value and \
                                        n.is_derived_from(
                                            "tosca.nodes.BlockStorage"):
                                        volume_name = node_name
                                        break

                        if volume_name:
                            suffix = suffix + 1
                            attachment_node = self._get_attachment_node(
                                node, suffix, volume_name)
                            if attachment_node:
                                self.hot_resources.append(attachment_node)
                for i in self.tosca.inputs:
                    if (i.name == 'key_name' and
                            node.get_property_value('key_name') is None):
                        schema = {'type': i.type, 'default': i.default}
                        value = {"get_param": "key_name"}
                        prop = Property(i.name, value, schema)
                        node._properties.append(prop)

        for policy in self.policies:
            policy_type = policy.type_definition
            if policy.is_derived_from('tosca.policies.Scaling') and \
               policy_type.type != 'tosca.policies.Scaling.Cluster':
                TOSCA_TO_HOT_TYPE[policy_type.type] = \
                    TOSCA_TO_HOT_TYPE['tosca.policies.Scaling']
            if policy.is_derived_from('tosca.policies.Monitoring'):
                TOSCA_TO_HOT_TYPE[policy_type.type] = \
                    TOSCA_TO_HOT_TYPE['tosca.policies.Monitoring']
            if policy.is_derived_from('tosca.policies.Placement'):
                TOSCA_TO_HOT_TYPE[policy_type.type] = \
                    TOSCA_TO_HOT_TYPE['tosca.policies.Placement']
            if policy.is_derived_from('tosca.policies.Reservation'):
                TOSCA_TO_HOT_TYPE[policy_type.type] = \
                    TOSCA_TO_HOT_TYPE['tosca.policies.Reservation']
            if policy_type.type not in TOSCA_TO_HOT_TYPE:
                raise UnsupportedTypeError(type=_('%s') % policy_type.type)
            elif policy_type.type == 'tosca.policies.Scaling.Cluster':
                self.hot_template_version = '2016-04-08'
            if policy.is_derived_from('tosca.policies.Scaling') and \
               policy_type.type != 'tosca.policies.Scaling.Cluster':
                policy_node = TOSCA_TO_HOT_TYPE[policy_type.type](
                    policy,
                    hot_template_parameters=self.hot_template.parameters)
            else:
                policy_node = TOSCA_TO_HOT_TYPE[policy_type.type](policy)
            self.hot_resources.append(policy_node)

        # Handle life cycle operations: this may expand each node
        # into multiple HOT resources and may change their name
        lifecycle_resources = []
        for resource in self.hot_resources:
            expanded_resources, deploy_lookup, last_deploy = resource.\
                handle_life_cycle()
            if expanded_resources:
                lifecycle_resources += expanded_resources
            if deploy_lookup:
                self.hot_lookup.update(deploy_lookup)
            if last_deploy:
                self.last_deploy_map[resource] = last_deploy
        self.hot_resources += lifecycle_resources

        # Handle configuration from ConnectsTo relationship in the TOSCA node:
        # this will generate multiple HOT resources, set of 2 for each
        # configuration
        connectsto_resources = []
        for node in self.nodetemplates:
            for requirement in node.requirements:
                for endpoint, details in requirement.items():
                    relation = None
                    if isinstance(details, dict):
                        target = details.get('node')
                        relation = details.get('relationship')
                    else:
                        target = details
                    if (target and relation and
                            not isinstance(relation, six.string_types)):
                        interfaces = relation.get('interfaces')
                        connectsto_resources += \
                            self._create_connect_configs(node,
                                                         target,
                                                         interfaces)
        self.hot_resources += connectsto_resources

        # Copy the initial dependencies based on the relationship in
        # the TOSCA template
        for node in self.nodetemplates:
            for node_depend in node.related_nodes:
                # if the source of dependency is a server and the
                # relationship type is 'tosca.relationships.HostedOn',
                # add dependency as properties.server
                base_type = HotResource.get_base_type_str(
                    node_depend.type_definition)
                if base_type == 'tosca.nodes.Compute' and \
                   node.related[node_depend].type == \
                   node.type_definition.HOSTEDON:
                    self.hot_lookup[node].properties['server'] = \
                        {'get_resource': self.hot_lookup[node_depend].name}
                # for all others, add dependency as depends_on
                else:
                    self.hot_lookup[node].depends_on.append(
                        self.hot_lookup[node_depend].top_of_chain())

                self.hot_lookup[node].depends_on_nodes.append(
                    self.hot_lookup[node_depend].top_of_chain())

                last_deploy = self.last_deploy_map.get(
                    self.hot_lookup[node_depend])
                if last_deploy and \
                    last_deploy not in self.hot_lookup[node].depends_on:
                    self.hot_lookup[node].depends_on.append(last_deploy)
                    self.hot_lookup[node].depends_on_nodes.append(last_deploy)

        # handle hosting relationship
        for resource in self.hot_resources:
            resource.handle_hosting()

        # handle built-in properties of HOT resources
        # if a resource depends on other resources,
        # their properties need to be handled first.
        # Use recursion to handle the properties of the
        # dependent nodes in correct order
        self.processed_resources = []
        for resource in self.hot_resources:
            if resource.type not in HOT_SCALING_POLICY_TYPE:
                self._recursive_handle_properties(resource)

        # handle resources that need to expand to more than one HOT resource
        expansion_resources = []
        for resource in self.hot_resources:
            expanded = resource.handle_expansion()
            if expanded:
                expansion_resources += expanded
        self.hot_resources += expansion_resources

        # Resolve function calls:  GetProperty, GetAttribute, GetInput
        # at this point, all the HOT resources should have been created
        # in the graph.
        for resource in self.hot_resources:
            # traverse the reference chain to get the actual value
            inputs = resource.properties.get('input_values')
            if inputs:
                for name, value in inputs.items():
                    inputs[name] = self.translate_param_value(value, resource)

        # remove resources without type defined
        # for example a SoftwareComponent without interfaces
        # would fall in this case
        to_remove = []
        for resource in self.hot_resources:
            if resource.type is None:
                to_remove.append(resource)

        for resource in to_remove:
            self.hot_resources.remove(resource)

        for resource in self.hot_resources:
            for removed_resource in to_remove:
                if removed_resource in resource.depends_on:
                    resource.depends_on.remove(removed_resource)

        return self.hot_resources

    def translate_param_value(self, param_value, resource):
        tosca_template = None
        if resource:
            tosca_template = resource.nodetemplate

        get_property_args = None
        if isinstance(param_value, GetProperty):
            get_property_args = param_value.args
        # to remove when the parser is fixed to return GetProperty
        elif isinstance(param_value, dict) and 'get_property' in param_value:
            get_property_args = param_value['get_property']
        if get_property_args is not None:
            tosca_target, prop_name, prop_arg = \
                self.decipher_get_operation(get_property_args,
                                            tosca_template)
            if tosca_target:
                prop_value = tosca_target.get_property_value(prop_name)
                if prop_value is not None:
                    prop_value = self.translate_param_value(
                        prop_value, resource)
                    return self._unfold_value(prop_value, prop_arg)
        get_attr_args = None
        if isinstance(param_value, GetAttribute):
            get_attr_args = param_value.result().args
        # to remove when the parser is fixed to return GetAttribute
        elif isinstance(param_value, dict) and 'get_attribute' in param_value:
            get_attr_args = param_value['get_attribute']
        if get_attr_args is not None:
            # for the attribute
            # get the proper target type to perform the translation
            tosca_target, attr_name, attr_arg = \
                self.decipher_get_operation(get_attr_args, tosca_template)
            attr_args = []
            if attr_arg:
                attr_args += attr_arg
            if tosca_target:
                if tosca_target in self.hot_lookup:
                    attr_value = self.hot_lookup[tosca_target].\
                        get_hot_attribute(attr_name, attr_args)
                    attr_value = self.translate_param_value(
                        attr_value, resource)
                    return self._unfold_value(attr_value, attr_arg)
        elif isinstance(param_value, dict) and 'get_artifact' in param_value:
            get_artifact_args = param_value['get_artifact']
            tosca_target, artifact_name, _ = \
                self.decipher_get_operation(get_artifact_args,
                                            tosca_template)

            if tosca_target:
                artifacts = HotResource.get_all_artifacts(tosca_target)
                if artifact_name in artifacts:
                    cwd = os.getcwd()
                    artifact = artifacts[artifact_name]
                    if self.csar_dir:
                        os.chdir(self.csar_dir)
                        get_file = os.path.abspath(artifact.get('file'))
                    else:
                        get_file = artifact.get('file')
                    if artifact.get('type', None) == 'tosca.artifacts.File':
                        return {'get_file': get_file}
            os.chdir(cwd)
        get_input_args = None
        if isinstance(param_value, GetInput):
            get_input_args = param_value.args
        elif isinstance(param_value, dict) and 'get_input' in param_value:
            get_input_args = param_value['get_input']
        if get_input_args is not None:
            if isinstance(get_input_args, list) \
                    and len(get_input_args) == 1:
                return {'get_param': self.translate_param_value(
                    get_input_args[0], resource)}
            else:
                return {'get_param': self.translate_param_value(
                    get_input_args, resource)}
        elif isinstance(param_value, GetOperationOutput):
            res = self._translate_get_operation_output_function(
                param_value.args, tosca_template)
            if res:
                return res
        elif isinstance(param_value, dict) \
                and 'get_operation_output' in param_value:
            res = self._translate_get_operation_output_function(
                param_value['get_operation_output'], tosca_template)
            if res:
                return res
        concat_list = None
        if isinstance(param_value, Concat):
            concat_list = param_value.args
        elif isinstance(param_value, dict) and 'concat' in param_value:
            concat_list = param_value['concat']
        if concat_list is not None:
            res = self._translate_concat_function(concat_list, resource)
            if res:
                return res

        if isinstance(param_value, list):
            translated_list = []
            for elem in param_value:
                translated_elem = self.translate_param_value(elem, resource)
                if translated_elem:
                    translated_list.append(translated_elem)
            return translated_list

        if isinstance(param_value, BASE_TYPES):
            return param_value

        return None

    def _translate_concat_function(self, concat_list, resource):
        str_replace_template = ''
        str_replace_params = {}
        index = 0
        for elem in concat_list:
            str_replace_template += '$s' + str(index)
            str_replace_params['$s' + str(index)] = \
                self.translate_param_value(elem, resource)
            index += 1

        return {'str_replace': {
            'template': str_replace_template,
            'params': str_replace_params
        }}

    def _translate_get_operation_output_function(self, args, tosca_template):
        tosca_target = self._find_tosca_node(args[0],
                                             tosca_template)
        if tosca_target and len(args) >= 4:
            operations = HotResource.get_all_operations(tosca_target)
            # ignore Standard interface name,
            # it is the only one supported in the translator anyway
            op_name = args[2]
            output_name = args[3]
            if op_name in operations:
                operation = operations[op_name]
                if operation in self.hot_lookup:
                    matching_deploy = self.hot_lookup[operation]
                    matching_config_name = matching_deploy.\
                        properties['config']['get_resource']
                    matching_config = self.find_hot_resource(
                        matching_config_name)
                    if matching_config:
                        outputs = matching_config.properties.get('outputs')
                        if outputs is None:
                            outputs = []
                        outputs.append({'name': output_name})
                        matching_config.properties['outputs'] = outputs
                    return {'get_attr': [
                        matching_deploy.name,
                        output_name
                    ]}

    @staticmethod
    def _unfold_value(value, value_arg):
        if value_arg is not None:
            if isinstance(value, dict):
                val = value.get(value_arg)
                if val is not None:
                    return val

            index = utils.str_to_num(value_arg)
            if isinstance(value, list) and index is not None:
                return value[index]
        return value

    def decipher_get_operation(self, args, current_tosca_node):
        tosca_target = self._find_tosca_node(args[0],
                                             current_tosca_node)
        new_target = None
        if tosca_target and len(args) > 2:
            cap_or_req_name = args[1]
            cap = tosca_target.get_capability(cap_or_req_name)
            if cap:
                new_target = cap
            else:
                for req in tosca_target.requirements:
                    if cap_or_req_name in req:
                        new_target = self._find_tosca_node(
                            req[cap_or_req_name])
                        cap = new_target.get_capability(cap_or_req_name)
                        if cap:
                            new_target = cap
                        break

        if new_target:
            tosca_target = new_target

            prop_name = args[2]
            prop_arg = args[3] if len(args) >= 4 else None
        else:
            prop_name = args[1]
            prop_arg = args[2] if len(args) >= 3 else None

        return tosca_target, prop_name, prop_arg

    def _get_attachment_node(self, node, suffix, volume_name):
        attach = False
        ntpl = self.nodetemplates
        for key_r, value_n in node.relationships.items():
            if key_r.is_derived_from('tosca.relationships.AttachesTo'):
                if value_n.is_derived_from('tosca.nodes.BlockStorage'):
                    if volume_name == value_n.name:
                        attach = True
            if attach:
                relationship_tpl = None
                for req in node.requirements:
                    for key, val in req.items():
                        if isinstance(val, dict):
                            if value_n.name != val.get('node'):
                                continue
                        else:
                            if value_n.name != val:
                                continue
                        attach = val
                        relship = val.get('relationship')
                        for rkey, rval in val.items():
                            if relship and isinstance(relship, dict):
                                for rkey, rval in relship.items():
                                    if rkey == 'type':
                                        relationship_tpl = val
                                        attach = rval
                                    elif rkey == 'template':
                                        rel_tpl_list = \
                                            (self.tosca.topology_template.
                                             _tpl_relationship_templates())
                                        relationship_tpl = rel_tpl_list[rval]
                                        attach = rval
                                    else:
                                        continue
                            elif isinstance(relship, str):
                                attach = relship
                                relationship_tpl = val
                                relationship_templates = \
                                    self.tosca._tpl_relationship_templates()
                                if 'relationship' in relationship_tpl and \
                                   attach not in \
                                   self.tosca._tpl_relationship_types() and \
                                   attach in relationship_templates:
                                    relationship_tpl['relationship'] = \
                                        relationship_templates[attach]
                                break
                        if relationship_tpl:
                            rval_new = attach + "_" + str(suffix)
                            att = RelationshipTemplate(
                                relationship_tpl, rval_new,
                                self.tosca._tpl_relationship_types())
                            hot_node = ToscaBlockStorageAttachment(att, ntpl,
                                                                   node.name,
                                                                   volume_name
                                                                   )
                            return hot_node

    def find_hot_resource(self, name):
        for resource in self.hot_resources:
            if resource.name == name:
                return resource

    def _find_tosca_node(self, tosca_name, current_tosca_template=None):
        tosca_node = None
        if tosca_name == 'SELF':
            tosca_node = current_tosca_template
        if tosca_name == 'HOST' and current_tosca_template:
            for req in current_tosca_template.requirements:
                if 'host' in req:
                    tosca_node = self._find_tosca_node(req['host'])

        if tosca_node is None:
            for node in self.nodetemplates:
                if node.name == tosca_name:
                    tosca_node = node
                    break
        return tosca_node

    def _find_hot_resource_for_tosca(self, tosca_name,
                                     current_hot_resource=None):
        current_tosca_resource = current_hot_resource.nodetemplate \
            if current_hot_resource else None
        tosca_node = self._find_tosca_node(tosca_name, current_tosca_resource)
        if tosca_node:
            return self.hot_lookup[tosca_node]

        return None

    def _create_connect_configs(self, source_node, target_name,
                                connect_interfaces):
        connectsto_resources = []
        if connect_interfaces:
            for iname, interface in connect_interfaces.items():
                connectsto_resources += \
                    self._create_connect_config(source_node, target_name,
                                                interface)
        return connectsto_resources

    def _create_connect_config(self, source_node, target_name,
                               connect_interface):
        connectsto_resources = []
        target_node = self._find_tosca_node(target_name)
        # the configuration can occur on the source or the target
        connect_config = connect_interface.get('pre_configure_target')
        if connect_config is not None:
            config_location = 'target'
        else:
            connect_config = connect_interface.get('pre_configure_source')
            if connect_config is not None:
                config_location = 'source'
            else:
                msg = _("Template error:  "
                        "no configuration found for ConnectsTo "
                        "in {1}").format(self.nodetemplate.name)
                log.error(msg)
                raise Exception(msg)
        config_name = source_node.name + '_' + target_name + '_connect_config'
        implement = connect_config.get('implementation')
        cwd = os.getcwd()
        if config_location == 'target':
            if self.csar_dir:
                os.chdir(self.csar_dir)
                get_file = os.path.abspath(implement)
            else:
                get_file = implement
            hot_config = HotResource(target_node,
                                     config_name,
                                     'OS::Heat::SoftwareConfig',
                                     {'config': {'get_file': get_file}},
                                     csar_dir=self.csar_dir)
        elif config_location == 'source':
            if self.csar_dir:
                os.chdir(self.csar_dir)
                get_file = os.path.abspath(implement)
            else:
                get_file = implement
            hot_config = HotResource(source_node,
                                     config_name,
                                     'OS::Heat::SoftwareConfig',
                                     {'config': {'get_file': get_file}},
                                     csar_dir=self.csar_dir)
        os.chdir(cwd)
        connectsto_resources.append(hot_config)
        hot_target = self._find_hot_resource_for_tosca(target_name)
        hot_source = self._find_hot_resource_for_tosca(source_node.name)
        connectsto_resources.append(hot_config.
                                    handle_connectsto(source_node,
                                                      target_node,
                                                      hot_source,
                                                      hot_target,
                                                      config_location,
                                                      connect_interface))
        return connectsto_resources

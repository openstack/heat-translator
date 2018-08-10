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
import logging
import os
import six

from toscaparser.elements.interfaces import InterfacesDef
from toscaparser.functions import GetInput
from toscaparser.nodetemplate import NodeTemplate
from toscaparser.utils.gettextutils import _


SECTIONS = (TYPE, PROPERTIES, MEDADATA, DEPENDS_ON, UPDATE_POLICY,
            DELETION_POLICY) = \
           ('type', 'properties', 'metadata',
            'depends_on', 'update_policy', 'deletion_policy')

policy_type = ['tosca.policies.Placement',
               'tosca.policies.Scaling',
               'tosca.policies.Scaling.Cluster',
               'tosca.policies.Monitoring',
               'tosca.policies.Reservation']
log = logging.getLogger('heat-translator')


class HotResource(object):
    '''Base class for TOSCA node type translation to Heat resource type.'''

    def __init__(self, nodetemplate, name=None, type=None, properties=None,
                 metadata=None, depends_on=None,
                 update_policy=None, deletion_policy=None, csar_dir=None):
        log.debug(_('Translating TOSCA node type to HOT resource type.'))
        self.nodetemplate = nodetemplate
        if name:
            self.name = name
        else:
            self.name = nodetemplate.name
        self.type = type
        self.properties = properties or {}

        self.csar_dir = csar_dir
        # special case for HOT softwareconfig
        cwd = os.getcwd()
        if type == 'OS::Heat::SoftwareConfig':
            config = self.properties.get('config')
            if isinstance(config, dict):
                if self.csar_dir:
                    os.chdir(self.csar_dir)
                    implementation_artifact = os.path.abspath(config.get(
                        'get_file'))
                else:
                    implementation_artifact = config.get('get_file')
                if implementation_artifact:
                    filename, file_extension = os.path.splitext(
                        implementation_artifact)
                    file_extension = file_extension.lower()
                    # artifact_types should be read to find the exact script
                    # type, unfortunately artifact_types doesn't seem to be
                    # supported by the parser
                    if file_extension == '.ansible' \
                            or file_extension == '.yaml' \
                            or file_extension == '.yml':
                        self.properties['group'] = 'ansible'
                    if file_extension == '.pp':
                        self.properties['group'] = 'puppet'

            if self.properties.get('group') is None:
                self.properties['group'] = 'script'
        os.chdir(cwd)
        self.metadata = metadata

        # The difference between depends_on and depends_on_nodes is
        # that depends_on defines dependency in the context of the
        # HOT template and it is used during the template output.
        # Depends_on_nodes defines the direct dependency between the
        # tosca nodes and is not used during the output of the
        # HOT template but for internal processing only. When a tosca
        # node depends on another node it will be always added to
        # depends_on_nodes but not always to depends_on. For example
        # if the source of dependency is a server, the dependency will
        # be added as properties.get_resource and not depends_on
        if depends_on:
            self.depends_on = depends_on
            self.depends_on_nodes = depends_on
        else:
            self.depends_on = []
            self.depends_on_nodes = []
        self.update_policy = update_policy
        self.deletion_policy = deletion_policy
        self.group_dependencies = {}
        # if hide_resource is set to true, then this resource will not be
        # generated in the output yaml.
        self.hide_resource = False

    def handle_properties(self):
        # the property can hold a value or the intrinsic function get_input
        # for value, copy it
        # for get_input, convert to get_param
        for prop in self.nodetemplate.get_properties_objects():
            pass

    def handle_life_cycle(self):
        hot_resources = []
        deploy_lookup = {}
        # TODO(anyone):  sequence for life cycle needs to cover different
        # scenarios and cannot be fixed or hard coded here
        operations_deploy_sequence = ['create', 'configure', 'start']

        operations = HotResource.get_all_operations(self.nodetemplate)

        # create HotResource for each operation used for deployment:
        # create, start, configure
        # ignore the other operations
        # observe the order:  create, start, configure
        # use the current HotResource for the first operation in this order

        # hold the original name since it will be changed during
        # the transformation
        node_name = self.name
        reserve_current = 'NONE'

        for operation in operations_deploy_sequence:
            if operation in operations.keys():
                reserve_current = operation
                break

        # create the set of SoftwareDeployment and SoftwareConfig for
        # the interface operations
        hosting_server = None
        if self.nodetemplate.requirements is not None:
            hosting_server = self._get_hosting_server()

        sw_deployment_resource = HOTSoftwareDeploymentResources(hosting_server)
        server_key = sw_deployment_resource.server_key
        servers = sw_deployment_resource.servers
        sw_deploy_res = sw_deployment_resource.software_deployment

        # hosting_server is None if requirements is None
        hosting_on_server = hosting_server if hosting_server else None
        base_type = HotResource.get_base_type_str(
            self.nodetemplate.type_definition)
        # if we are on a compute node the host is self
        if hosting_on_server is None and base_type == 'tosca.nodes.Compute':
            hosting_on_server = self.name
            servers = {'get_resource': self.name}

        cwd = os.getcwd()
        for operation in operations.values():
            if operation.name in operations_deploy_sequence:
                config_name = node_name + '_' + operation.name + '_config'
                deploy_name = node_name + '_' + operation.name + '_deploy'
                if self.csar_dir:
                    os.chdir(self.csar_dir)
                    get_file = os.path.abspath(operation.implementation)
                else:
                    get_file = operation.implementation
                hot_resources.append(
                    HotResource(self.nodetemplate,
                                config_name,
                                'OS::Heat::SoftwareConfig',
                                {'config':
                                    {'get_file': get_file}},
                                csar_dir=self.csar_dir))
                if operation.name == reserve_current and \
                    base_type != 'tosca.nodes.Compute':
                    deploy_resource = self
                    self.name = deploy_name
                    self.type = sw_deploy_res
                    self.properties = {'config': {'get_resource': config_name},
                                       server_key: servers}
                    deploy_lookup[operation] = self
                else:
                    sd_config = {'config': {'get_resource': config_name},
                                 server_key: servers}
                    deploy_resource = \
                        HotResource(self.nodetemplate,
                                    deploy_name,
                                    sw_deploy_res,
                                    sd_config, csar_dir=self.csar_dir)
                    hot_resources.append(deploy_resource)
                    deploy_lookup[operation] = deploy_resource
                lifecycle_inputs = self._get_lifecycle_inputs(operation)
                if lifecycle_inputs:
                    deploy_resource.properties['input_values'] = \
                        lifecycle_inputs
        os.chdir(cwd)

        # Add dependencies for the set of HOT resources in the sequence defined
        # in operations_deploy_sequence
        # TODO(anyone): find some better way to encode this implicit sequence
        group = {}
        op_index_min = None
        op_index_max = -1
        for op, hot in deploy_lookup.items():
            # position to determine potential preceding nodes
            op_index = operations_deploy_sequence.index(op.name)
            if op_index_min is None or op_index < op_index_min:
                op_index_min = op_index
            if op_index > op_index_max:
                op_index_max = op_index
            for preceding_op_name in \
                    reversed(operations_deploy_sequence[:op_index]):
                preceding_hot = deploy_lookup.get(
                    operations.get(preceding_op_name))
                if preceding_hot:
                    hot.depends_on.append(preceding_hot)
                    hot.depends_on_nodes.append(preceding_hot)
                    group[preceding_hot] = hot
                    break

        if op_index_max >= 0:
            last_deploy = deploy_lookup.get(operations.get(
                operations_deploy_sequence[op_index_max]))
        else:
            last_deploy = None

        # save this dependency chain in the set of HOT resources
        self.group_dependencies.update(group)
        for hot in hot_resources:
            hot.group_dependencies.update(group)

        roles_deploy_resource = self._handle_ansiblegalaxy_roles(
            hot_resources, node_name, servers)

        # add a dependency to this ansible roles deploy to
        # the first "classic" deploy generated for this node
        if roles_deploy_resource and op_index_min:
            first_deploy = deploy_lookup.get(operations.get(
                operations_deploy_sequence[op_index_min]))
            first_deploy.depends_on.append(roles_deploy_resource)
            first_deploy.depends_on_nodes.append(roles_deploy_resource)

        return hot_resources, deploy_lookup, last_deploy

    def _handle_ansiblegalaxy_roles(self, hot_resources, initial_node_name,
                                    hosting_on_server):
        artifacts = self.get_all_artifacts(self.nodetemplate)
        install_roles_script = ''

        sw_deployment_resource = \
            HOTSoftwareDeploymentResources(hosting_on_server)
        server_key = sw_deployment_resource.server_key
        sw_deploy_res = sw_deployment_resource.software_deployment
        for artifact_name, artifact in artifacts.items():
            artifact_type = artifact.get('type', '').lower()
            if artifact_type == 'tosca.artifacts.ansiblegalaxy.role':
                role = artifact.get('file', None)
                if role:
                    install_roles_script += 'ansible-galaxy install ' + role \
                                            + '\n'

        if install_roles_script:
            # remove trailing \n
            install_roles_script = install_roles_script[:-1]
            # add shebang and | to use literal scalar type (for multiline)
            install_roles_script = '|\n#!/bin/bash\n' + install_roles_script

            config_name = initial_node_name + '_install_roles_config'
            deploy_name = initial_node_name + '_install_roles_deploy'
            hot_resources.append(
                HotResource(self.nodetemplate, config_name,
                            'OS::Heat::SoftwareConfig',
                            {'config': install_roles_script},
                            csar_dir=self.csar_dir))
            sd_config = {'config': {'get_resource': config_name},
                         server_key: hosting_on_server}
            deploy_resource = \
                HotResource(self.nodetemplate, deploy_name,
                            sw_deploy_res,
                            sd_config, csar_dir=self.csar_dir)
            hot_resources.append(deploy_resource)

            return deploy_resource

    def handle_connectsto(self, tosca_source, tosca_target, hot_source,
                          hot_target, config_location, operation):
        # The ConnectsTo relationship causes a configuration operation in
        # the target.
        # This hot resource is the software config portion in the HOT template
        # This method adds the matching software deployment with the proper
        # target server and dependency
        if config_location == 'target':
            hosting_server = hot_target._get_hosting_server()
            hot_depends = hot_target
        elif config_location == 'source':
            hosting_server = self._get_hosting_server()
            hot_depends = hot_source
        sw_deployment_resource = HOTSoftwareDeploymentResources(hosting_server)
        server_key = sw_deployment_resource.server_key
        servers = sw_deployment_resource.servers
        sw_deploy_res = sw_deployment_resource.software_deployment

        deploy_name = tosca_source.name + '_' + tosca_target.name + \
            '_connect_deploy'
        sd_config = {'config': {'get_resource': self.name},
                     server_key: servers}
        deploy_resource = \
            HotResource(self.nodetemplate,
                        deploy_name,
                        sw_deploy_res,
                        sd_config,
                        depends_on=[hot_depends], csar_dir=self.csar_dir)
        connect_inputs = self._get_connect_inputs(config_location, operation)
        if connect_inputs:
            deploy_resource.properties['input_values'] = connect_inputs

        return deploy_resource

    def handle_expansion(self):
        pass

    def handle_hosting(self):
        # handle hosting server for the OS:HEAT::SoftwareDeployment
        # from the TOSCA nodetemplate, traverse the relationship chain
        # down to the server
        sw_deploy_group = \
            HOTSoftwareDeploymentResources.HOT_SW_DEPLOYMENT_GROUP_RESOURCE
        sw_deploy = HOTSoftwareDeploymentResources.HOT_SW_DEPLOYMENT_RESOURCE

        if self.properties.get('servers') and \
                self.properties.get('server'):
            del self.properties['server']
        if self.type == sw_deploy_group or self.type == sw_deploy:
            # skip if already have hosting
            # If type is NodeTemplate, look up corresponding HotResrouce
            host_server = self.properties.get('servers') \
                or self.properties.get('server')
            if host_server is None:
                raise Exception(_("Internal Error: expecting host "
                                  "in software deployment"))

            elif isinstance(host_server.get('get_resource'), NodeTemplate):
                self.properties['server']['get_resource'] = \
                    host_server['get_resource'].name

            elif isinstance(host_server, dict) and \
                not host_server.get('get_resource'):
                self.properties['servers'] = \
                    host_server

    def top_of_chain(self):
        dependent = self.group_dependencies.get(self)
        if dependent is None:
            return self
        else:
            return dependent.top_of_chain()

    # this function allows to provides substacks as external files
    # those files will be dumped along the output file.
    #
    # return a dict of filename-content
    def extract_substack_templates(self, base_filename, hot_template_version):
        return {}

    # this function asks the resource to embed substacks
    # into the main template, if any.
    # this is used when the final output is stdout
    def embed_substack_templates(self, hot_template_version):
        pass

    def get_dict_output(self):
        resource_sections = OrderedDict()
        resource_sections[TYPE] = self.type
        if self.properties:
            resource_sections[PROPERTIES] = self.properties
        if self.metadata:
            resource_sections[MEDADATA] = self.metadata
        if self.depends_on:
            resource_sections[DEPENDS_ON] = []
            for depend in self.depends_on:
                resource_sections[DEPENDS_ON].append(depend.name)
        if self.update_policy:
            resource_sections[UPDATE_POLICY] = self.update_policy
        if self.deletion_policy:
            resource_sections[DELETION_POLICY] = self.deletion_policy

        return {self.name: resource_sections}

    def _get_lifecycle_inputs(self, operation):
        # check if this lifecycle operation has input values specified
        # extract and convert to HOT format
        if isinstance(operation.value, six.string_types):
            # the operation has a static string
            return {}
        else:
            # the operation is a dict {'implemenation': xxx, 'input': yyy}
            inputs = operation.value.get('inputs')
            deploy_inputs = {}
            if inputs:
                for name, value in inputs.items():
                    deploy_inputs[name] = value
            return deploy_inputs

    def _get_connect_inputs(self, config_location, operation):
        if config_location == 'target':
            inputs = operation.get('pre_configure_target').get('inputs')
        elif config_location == 'source':
            inputs = operation.get('pre_configure_source').get('inputs')
        deploy_inputs = {}
        if inputs:
            for name, value in inputs.items():
                deploy_inputs[name] = value
        return deploy_inputs

    def _get_hosting_server(self, node_template=None):
        # find the server that hosts this software by checking the
        # requirements and following the hosting chain
        hosting_servers = []
        host_exists = False
        this_node_template = self.nodetemplate \
            if node_template is None else node_template
        for requirement in this_node_template.requirements:
            for requirement_name, assignment in requirement.items():
                for check_node in this_node_template.related_nodes:
                    # check if the capability is Container
                    if isinstance(assignment, dict):
                        node_name = assignment.get('node')
                    else:
                        node_name = assignment
                    if node_name and node_name == check_node.name:
                        if self._is_container_type(requirement_name,
                                                   check_node):
                            hosting_servers.append(check_node.name)
                            host_exists = True
                        elif check_node.related_nodes and not host_exists:
                            return self._get_hosting_server(check_node)
        if hosting_servers:
            return hosting_servers
        return None

    def _is_container_type(self, requirement_name, node):
        # capability is a list of dict
        # For now just check if it's type tosca.nodes.Compute
        # TODO(anyone): match up requirement and capability
        base_type = HotResource.get_base_type_str(node.type_definition)
        if base_type == 'tosca.nodes.Compute':
            return True
        else:
            return False

    def get_hot_attribute(self, attribute, args):
        # this is a place holder and should be implemented by the subclass
        # if translation is needed for the particular attribute
        raise Exception(_("No translation in TOSCA type {0} for attribute "
                          "{1}").format(self.nodetemplate.type, attribute))

    def get_tosca_props(self):
        tosca_props = {}
        for prop in self.nodetemplate.get_properties_objects():
            if isinstance(prop.value, GetInput):
                tosca_props[prop.name] = {'get_param': prop.value.input_name}
            else:
                tosca_props[prop.name] = prop.value
        return tosca_props

    @staticmethod
    def get_all_artifacts(nodetemplate):
        # workaround bug in the parser
        base_type = HotResource.get_base_type_str(nodetemplate.type_definition)
        if base_type in policy_type:
            artifacts = {}
        else:
            artifacts = nodetemplate.type_definition.get_value('artifacts',
                                                               parent=True)
        if not artifacts:
            artifacts = {}
        tpl_artifacts = nodetemplate.entity_tpl.get('artifacts')
        if tpl_artifacts:
            artifacts.update(tpl_artifacts)

        return artifacts

    @staticmethod
    def get_all_operations(node):
        operations = {}
        for operation in node.interfaces:
            operations[operation.name] = operation

        # workaround bug in the parser
        base_type = HotResource.get_base_type_str(node.type_definition)
        if base_type in policy_type:
            return operations

        node_type = node.type_definition

        while True:
            type_operations = HotResource._get_interface_operations_from_type(
                node_type, node, 'Standard')
            type_operations.update(operations)
            operations = type_operations

            if node_type.parent_type is not None:
                node_type = node_type.parent_type
            else:
                return operations

    @staticmethod
    def _get_interface_operations_from_type(node_type, node, lifecycle_name):
        operations = {}
        base_type = HotResource.get_base_type_str(node_type)
        if base_type in policy_type:
            return operations
        if node_type.interfaces and lifecycle_name in node_type.interfaces:
            for name, elems in node_type.interfaces[lifecycle_name].items():
                # ignore empty operations (only type)
                # ignore global interface inputs,
                # concrete inputs are on the operations themselves
                if name != 'type' and name != 'inputs':
                    operations[name] = InterfacesDef(node_type,
                                                     lifecycle_name,
                                                     node, name, elems)
        return operations

    @staticmethod
    def get_base_type_str(node_type):
        if isinstance(node_type, six.string_types):
            return node_type
        if node_type.parent_type is not None:
            parent_type_str = None
            if isinstance(node_type.parent_type, six.string_types):
                parent_type_str = node_type.parent_type
            else:
                parent_type_str = node_type.parent_type.type

            if parent_type_str and parent_type_str.endswith('.Root'):
                return node_type.type
            else:
                return HotResource.get_base_type_str(node_type.parent_type)

        return node_type.type


class HOTSoftwareDeploymentResources(object):
    """Provides HOT Software Deployment resources

    SoftwareDeployment or SoftwareDeploymentGroup Resource
    """

    HOT_SW_DEPLOYMENT_RESOURCE = 'OS::Heat::SoftwareDeployment'
    HOT_SW_DEPLOYMENT_GROUP_RESOURCE = 'OS::Heat::SoftwareDeploymentGroup'

    def __init__(self, hosting_server=None):
        self.software_deployment = self.HOT_SW_DEPLOYMENT_RESOURCE
        self.software_deployment_group = self.HOT_SW_DEPLOYMENT_GROUP_RESOURCE
        self.server_key = 'server'
        self.hosting_server = hosting_server
        self.servers = {}
        if hosting_server is not None:
            if len(self.hosting_server) == 1:
                if isinstance(hosting_server, list):
                    self.servers['get_resource'] = self.hosting_server[0]
            else:
                for server in self.hosting_server:
                    self.servers[server] = {'get_resource': server}
                self.software_deployment = self.software_deployment_group
                self.server_key = 'servers'

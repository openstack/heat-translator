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
import textwrap
from toscaparser.utils.gettextutils import _
import yaml

log = logging.getLogger('heat-translator')


class HotTemplate(object):
    '''Container for full Heat Orchestration template.'''

    SECTIONS = (VERSION, DESCRIPTION, PARAMETER_GROUPS, PARAMETERS,
                RESOURCES, OUTPUTS, MAPPINGS) = \
               ('heat_template_version', 'description', 'parameter_groups',
                'parameters', 'resources', 'outputs', '__undefined__')

    VERSIONS = (LATEST,) = ('2013-05-23',)

    def __init__(self):
        self.resources = []
        self.outputs = []
        self.parameters = []
        self.description = ""

    def represent_ordereddict(self, dumper, data):
        nodes = []
        for key, value in data.items():
            node_key = dumper.represent_data(key)
            node_value = dumper.represent_data(value)
            nodes.append((node_key, node_value))
        return yaml.nodes.MappingNode('tag:yaml.org,2002:map', nodes)

    def output_to_yaml_files_dict(self, base_filename,
                                  hot_template_version=LATEST):
        yaml_files_dict = {}
        base_filename, ext = os.path.splitext(base_filename)

        # convert from inlined substack to a substack defined in another file
        for resource in self.resources:
            yaml_files_dict.update(
                resource.extract_substack_templates(base_filename,
                                                    hot_template_version))

        yaml_files_dict[base_filename + ext] = \
            self.output_to_yaml(hot_template_version, False)

        return yaml_files_dict

    def output_to_yaml(self, hot_template_version=LATEST,
                       embed_substack_templates=True):
        log.debug(_('Converting translated output to yaml format.'))

        if embed_substack_templates:
            # fully inlined substack by storing the template as a blob string
            for resource in self.resources:
                resource.embed_substack_templates(hot_template_version)

        dict_output = OrderedDict()
        # Version
        version_string = self.VERSION + ": " + hot_template_version + "\n\n"

        # Description
        desc_str = ""
        if self.description:
            # Wrap the text to a new line if the line exceeds 80 characters.
            wrapped_txt = "\n  ".join(textwrap.wrap(self.description, 80))
            desc_str = self.DESCRIPTION + ": >\n  " + wrapped_txt + "\n\n"

        # Parameters
        all_params = OrderedDict()
        for parameter in self.parameters:
            all_params.update(parameter.get_dict_output())
        dict_output.update({self.PARAMETERS: all_params})

        # Resources
        all_resources = OrderedDict()
        for resource in self.resources:
            if not resource.hide_resource:
                all_resources.update(resource.get_dict_output())
        dict_output.update({self.RESOURCES: all_resources})

        # Outputs
        all_outputs = OrderedDict()
        for output in self.outputs:
            all_outputs.update(output.get_dict_output())
        dict_output.update({self.OUTPUTS: all_outputs})

        yaml.add_representer(OrderedDict, self.represent_ordereddict)
        yaml.add_representer(dict, self.represent_ordereddict)
        yaml_string = yaml.dump(dict_output, default_flow_style=False)
        # get rid of the '' from yaml.dump around numbers
        # also replace double return lines with a single one
        # seems to be a bug in the serialization of multiline literal scalars
        yaml_string = yaml_string.replace('\'', '') .replace('\n\n', '\n')
        return version_string + desc_str + yaml_string

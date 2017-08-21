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
import six
from toscaparser.utils.gettextutils import _
from translator.hot.syntax.hot_template import HotTemplate
from translator.hot.translate_inputs import TranslateInputs
from translator.hot.translate_node_templates import TranslateNodeTemplates
from translator.hot.translate_outputs import TranslateOutputs

log = logging.getLogger('heat-translator')


class TOSCATranslator(object):
    '''Invokes translation methods.'''

    def __init__(self, tosca, parsed_params, deploy=None, csar_dir=None):
        super(TOSCATranslator, self).__init__()
        self.tosca = tosca
        self.hot_template = HotTemplate()
        self.parsed_params = parsed_params
        self.deploy = deploy
        self.csar_dir = csar_dir
        self.node_translator = None
        log.info(_('Initialized parmaters for translation.'))

    def _translate_to_hot_yaml(self):
        self._resolve_input()
        self.hot_template.description = self.tosca.description
        self.hot_template.parameters = self._translate_inputs()
        self.node_translator = TranslateNodeTemplates(self.tosca,
                                                      self.hot_template,
                                                      csar_dir=self.csar_dir)
        self.hot_template.resources = \
            self.node_translator.translate()
        self.hot_template.outputs = self._translate_outputs()
        if self.node_translator.hot_template_version is None:
            self.node_translator.hot_template_version = HotTemplate.LATEST

    def translate(self):
        """Translate to HOT YAML

        This method produces a translated output for main template.
        The nested template, if any referenced by main, will be created
        as a separate file.
        """
        self._translate_to_hot_yaml()

        # TODO(mvelten) go back to calling hot_template.output_to_yaml instead
        # for stdout once embed_substack_templates is correctly implemented
        # return self.hot_template.output_to_yaml(
        #     self.node_translator.hot_template_version)
        yaml_files = self.hot_template.output_to_yaml_files_dict(
            "output.yaml",
            self.node_translator.hot_template_version)
        for name, content in six.iteritems(yaml_files):
            if name != "output.yaml":
                with open(name, 'w+') as f:
                    f.write(content)

        return yaml_files["output.yaml"]

    def translate_to_yaml_files_dict(self, base_filename):
        """Translate to HOT YAML

        This method produces a translated output containing main and
        any nested templates referenced by main. This output can be
        programmatically stored into different files by using key as
        template name and value as template content.
        """
        self._translate_to_hot_yaml()
        return self.hot_template.output_to_yaml_files_dict(
            base_filename,
            self.node_translator.hot_template_version)

    def _translate_inputs(self):
        translator = TranslateInputs(self.tosca.inputs, self.parsed_params,
                                     self.deploy)
        return translator.translate()

    def _translate_outputs(self):
        translator = TranslateOutputs(self.tosca.outputs, self.node_translator)
        return translator.translate()

    # check all properties for all node and ensure they are resolved
    # to actual value
    def _resolve_input(self):
        for n in self.tosca.nodetemplates:
            for node_prop in n.get_properties_objects():
                if isinstance(node_prop.value, dict) \
                        and 'get_input' in node_prop.value:
                    try:
                        self.parsed_params[node_prop.value['get_input']]
                    except Exception:
                        msg = (_('Must specify all input values in \
                                TOSCA template, missing %s.') %
                               node_prop.value['get_input'])
                        log.error(msg)
                        raise ValueError(msg)

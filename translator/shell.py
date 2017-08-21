#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import argparse
import codecs
import logging
import logging.config
import os
import six
import sys
import uuid
import yaml
import zipfile

# NOTE(aloga): As per upstream developers requirement this needs to work
# without the clients, therefore we need to pass if we cannot import them
try:
    from keystoneauth1 import loading
except ImportError:
    keystone_client_avail = False
else:
    keystone_client_avail = True

try:
    import heatclient.client
except ImportError:
    heat_client_avail = False
else:
    heat_client_avail = True


from toscaparser.tosca_template import ToscaTemplate
from toscaparser.utils.gettextutils import _
from toscaparser.utils.urlutils import UrlUtils
from translator.common import flavors
from translator.common import images
from translator.common import utils
from translator.conf.config import ConfigProvider
from translator.hot.tosca_translator import TOSCATranslator

"""
Test the heat-translator translation from command line as:
#heat-translator
  --template-file=<path to the YAML template>
  --template-type=<type of template e.g. tosca>
  --parameters="purpose=test"
Takes three user arguments,
1. Path to the file that needs to be translated (required)
2. type of translation (e.g. tosca) (optional)
3. Input parameters (optional)

In order to use heat-translator to only validate template,
without actual translation, pass --validate-only=true along with
other required arguments.

"""
conf_file = ConfigProvider.get_translator_logging_file()
try:
    logging.config.fileConfig(conf_file)
except Exception:
    pass
log = logging.getLogger("heat-translator")


class TranslatorShell(object):

    SUPPORTED_TYPES = ['tosca']
    TOSCA_CSAR_META_DIR = "TOSCA-Metadata"

    def get_parser(self, argv):
        parser = argparse.ArgumentParser(prog="heat-translator")

        parser.add_argument('--template-file',
                            metavar='<filename>',
                            required=True,
                            help=_('Template file to load.'))

        parser.add_argument('--output-file',
                            metavar='<filename>',
                            help=_('Where to store the output file. If not '
                                   'passed, it will be printed to stdin.'))

        parser.add_argument('--template-type',
                            metavar='<input-template-type>',
                            choices=self.SUPPORTED_TYPES,
                            default='tosca',
                            help=(_('Template type to parse. Choose between '
                                    '%s.') % self.SUPPORTED_TYPES))

        parser.add_argument('--parameters',
                            metavar='<param1=val1;param2=val2;...>',
                            help=_('Optional input parameters.'))

        parser.add_argument('--validate-only',
                            action='store_true',
                            default=False,
                            help=_('Only validate input template, do not '
                                   'perform translation.'))

        parser.add_argument('--deploy',
                            action='store_true',
                            default=False,
                            help=_('Whether to deploy the generated template '
                                   'or not.'))

        parser.add_argument('--stack-name',
                            metavar='<stack-name>',
                            required=False,
                            help=_('The name to use for the Heat stack when '
                                   'deploy the generated template.'))

        self._append_global_identity_args(parser, argv)

        return parser

    def _append_global_identity_args(self, parser, argv):
        if not keystone_client_avail:
            return

        loading.register_session_argparse_arguments(parser)

        default_auth_plugin = 'password'
        if 'os-token' in argv:
            default_auth_plugin = 'token'
        loading.register_auth_argparse_arguments(
            parser, argv, default=default_auth_plugin)

    def main(self, argv):

        parser = self.get_parser(argv)
        (args, args_list) = parser.parse_known_args(argv)

        template_file = args.template_file
        template_type = args.template_type
        output_file = args.output_file
        validate_only = args.validate_only
        deploy = args.deploy
        stack_name = args.stack_name

        parsed_params = {}
        if args.parameters:
            parsed_params = self._parse_parameters(args.parameters)

        a_file = os.path.isfile(template_file)
        a_url = UrlUtils.validate_url(template_file) if not a_file else False
        if a_file or a_url:
            if validate_only:
                ToscaTemplate(template_file, parsed_params, a_file)
                msg = (_('The input "%(template_file)s" successfully passed '
                         'validation.') % {'template_file': template_file})
                print(msg)
            else:
                if keystone_client_avail:
                    try:
                        keystone_auth = (
                            loading.load_auth_from_argparse_arguments(args)
                        )
                        keystone_session = (
                            loading.load_session_from_argparse_arguments(
                                args,
                                auth=keystone_auth
                            )
                        )
                        images.SESSION = keystone_session
                        flavors.SESSION = keystone_session
                    except Exception:
                        keystone_session = None

                translator = self._get_translator(template_type,
                                                  template_file,
                                                  parsed_params, a_file,
                                                  deploy)

                if translator and deploy:
                    if not keystone_client_avail or not heat_client_avail:
                        raise RuntimeError(_('Could not find Heat or Keystone'
                                             'client to deploy, aborting '))
                    if not keystone_session:
                        raise RuntimeError(_('Impossible to login with '
                                             'Keystone to deploy on Heat, '
                                             'please check your credentials'))

                    file_name = os.path.basename(
                        os.path.splitext(template_file)[0])
                    self.deploy_on_heat(keystone_session, keystone_auth,
                                        translator, stack_name, file_name,
                                        parsed_params)

                self._write_output(translator, output_file)
        else:
            msg = (_('The path %(template_file)s is not a valid '
                     'file or URL.') % {'template_file': template_file})

            log.error(msg)
            raise ValueError(msg)

    def deploy_on_heat(self, session, auth, translator,
                       stack_name, file_name, parameters):
        endpoint = auth.get_endpoint(session, service_type="orchestration")
        heat_client = heatclient.client.Client('1',
                                               session=session,
                                               auth=auth,
                                               endpoint=endpoint)

        heat_stack_name = stack_name if stack_name else \
            'heat_' + file_name + '_' + str(uuid.uuid4()).split("-")[0]
        msg = _('Deploy the generated template, the stack name is %(name)s.')\
            % {'name': heat_stack_name}
        log.debug(msg)
        tpl = yaml.safe_load(translator.translate())

        # get all the values for get_file from a translated template
        get_files = []
        utils.get_dict_value(tpl, "get_file", get_files)
        files = {}
        if get_files:
            for file in get_files:
                with codecs.open(file, encoding='utf-8', errors='strict') \
                    as f:
                        text = f.read()
                        files[file] = text
        tpl['heat_template_version'] = str(tpl['heat_template_version'])
        self._create_stack(heat_client=heat_client,
                           stack_name=heat_stack_name,
                           template=tpl,
                           parameters=parameters,
                           files=files)

    def _create_stack(self, heat_client, stack_name, template, parameters,
                      files):
        if heat_client:
            heat_client.stacks.create(stack_name=stack_name,
                                      template=template,
                                      parameters=parameters,
                                      files=files)

    def _parse_parameters(self, parameter_list):
        parsed_inputs = {}

        # Parameters are semi-colon separated
        inputs = parameter_list.replace('"', '').split(';')
        # Each parameter should be an assignment
        for param in inputs:
            keyvalue = param.split('=')
            # Validate the parameter has both a name and value
            msg = _("'%(param)s' is not a well-formed parameter.") % {
                'param': param}
            if keyvalue.__len__() is 2:
                # Assure parameter name is not zero-length or whitespace
                stripped_name = keyvalue[0].strip()
                if not stripped_name:
                    log.error(msg)
                    raise ValueError(msg)
                # Add the valid parameter to the dictionary
                parsed_inputs[keyvalue[0]] = keyvalue[1]
            else:
                log.error(msg)
                raise ValueError(msg)
        return parsed_inputs

    def _get_translator(self, sourcetype, path, parsed_params, a_file, deploy):
        if sourcetype == "tosca":
            log.debug(_('Loading the tosca template.'))
            tosca = ToscaTemplate(path, parsed_params, a_file)
            csar_dir = None
            if deploy and zipfile.is_zipfile(path):
                # set CSAR directory to the root of TOSCA-Metadata
                csar_decompress = utils.decompress(path)
                csar_dir = os.path.join(csar_decompress,
                                        self.TOSCA_CSAR_META_DIR)
                msg = _("'%(csar)s' is the location of decompressed "
                        "CSAR file.") % {'csar': csar_dir}
                log.info(msg)
            translator = TOSCATranslator(tosca, parsed_params, deploy,
                                         csar_dir=csar_dir)
            log.debug(_('Translating the tosca template.'))
        return translator

    def _write_output(self, translator, output_file=None):
        if output_file:
            path, filename = os.path.split(output_file)
            yaml_files = translator.translate_to_yaml_files_dict(filename)
            for name, content in six.iteritems(yaml_files):
                with open(os.path.join(path, name), 'w+') as f:
                    f.write(content)
        else:
            print(translator.translate())


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    TranslatorShell().main(args)


if __name__ == '__main__':
    main()

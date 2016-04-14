#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

"""Translate action implementations"""

import logging
import logging.config
import os
import sys

from cliff import command

from toscaparser.tosca_template import ToscaTemplate
from toscaparser.utils.gettextutils import _
from translator.common.utils import UrlUtils
from translator.conf.config import ConfigProvider
from translator.hot.tosca_translator import TOSCATranslator
from translator.osc import utils

conf_file = ConfigProvider.get_translator_logging_file()
logging.config.fileConfig(conf_file)
log = logging.getLogger('heat-translator')


class TranslateTemplate(command.Command):

    """Translate a template"""

    auth_required = False

    def get_parser(self, prog_name):
        parser = super(TranslateTemplate, self).get_parser(prog_name)
        parser.add_argument(
            '--template-file',
            metavar='<template-file>',
            required=True,
            help='Path to the file that needs to be translated.')
        parser.add_argument(
            '--template-type',
            metavar='<template-type>',
            required=True,
            choices=['tosca'],
            help='Format of the template file.')
        parser.add_argument(
            '--output-file',
            metavar='<output-file>',
            help='Path to place the translated content.')
        parser.add_argument(
            '--parameter',
            metavar='<key=value>',
            action=utils.KeyValueAction,
            help='Set a property for this template '
                 '(repeat option to set multiple properties)',
        )
        parser.add_argument(
            '--validate-only',
            metavar='<true or false>',
            help='Set to true to only validate a template file.',
            default='false')
        return parser

    def take_action(self, parsed_args):
        log.debug(_('Translating the template with input parameters'
                    '(%s).'), parsed_args)
        output = None

        if parsed_args.parameter:
            parsed_params = parsed_args.parameter
        else:
            parsed_params = {}

        if parsed_args.template_type == "tosca":
            path = parsed_args.template_file
            a_file = os.path.isfile(path)
            a_url = UrlUtils.validate_url(path) if not a_file else False
            if a_file or a_url:
                validate = parsed_args.validate_only
                if validate and validate.lower() == "true":
                    ToscaTemplate(path, parsed_params, a_file)
                    msg = (_('The input "%(path)s" successfully passed '
                             'validation.') % {'path': path})
                    print(msg)
                else:
                    tosca = ToscaTemplate(path, parsed_params, a_file)
                    translator = TOSCATranslator(tosca, parsed_params)
                    output = translator.translate()
            else:
                msg = _('Could not find template file.')
                log.error(msg)
                sys.stdout.write(msg)
                raise SystemExit

        if output:
            if parsed_args.output_file:
                with open(parsed_args.output_file, 'w+') as f:
                    f.write(output)
            else:
                print(output)

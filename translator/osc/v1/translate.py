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

import logging.config
import os
import sys

from cliff import command

from toscaparser.tosca_template import ToscaTemplate
from translator.common.utils import UrlUtils
from translator.hot.tosca_translator import TOSCATranslator
from translator.osc import utils


class TranslateTemplate(command.Command):
    """Translate a template"""

    log = logging.getLogger('heat-translator' + '.TranslateTemplate')
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
        return parser

    def take_action(self, parsed_args):
        self.log.debug('take_action(%s)', parsed_args)

        if parsed_args.parameter:
            parsed_params = parsed_args.parameter
        else:
            parsed_params = {}

        if parsed_args.template_type == "tosca":
            path = parsed_args.template_file
            a_file = os.path.isfile(path)
            a_url = UrlUtils.validate_url(path) if not a_file else False
            if a_file or a_url:
                tosca = ToscaTemplate(path, parsed_params, a_file)
                translator = TOSCATranslator(tosca, parsed_params)
                output = translator.translate()
            else:
                sys.stdout.write('Could not find template file.')
                raise SystemExit

        if parsed_args.output_file:
            with open(parsed_args.output_file, 'w+') as f:
                f.write(output)
        else:
            print(output)

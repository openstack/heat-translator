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

'''
Exceptions for the TOSCA Translator package.
'''

from toscaparser.common.exception import TOSCAException
from toscaparser.utils.gettextutils import _


class ConfFileParseError(TOSCAException):
    msg_fmt = _('%(message)s')


class ConfOptionNotDefined(TOSCAException):
    msg_fmt = _('Option %(key)s in section %(section)s '
                'is not defined in conf file')


class ConfSectionNotDefined(TOSCAException):
    msg_fmt = _('Section %(section)s is not defined in conf file')


class ToscaModImportError(TOSCAException):
    msg_fmt = _('Unable to import module %(mod_name)s. '
                'Check to see that it exists and has no '
                'language definition errors.')


class ToscaClassImportError(TOSCAException):
    msg_fmt = _('Unable to import class %(name)s in '
                'module %(mod_name)s. Check to see that it '
                'exists and has no language definition errors.')


class ToscaClassAttributeError(TOSCAException):
    msg_fmt = _('Class attribute referenced not found. '
                '%(message)s. Check to see that it is defined.')

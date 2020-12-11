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


import json
import logging
import math
import numbers
import os
import re
import requests
import tempfile
from urllib.parse import urlparse
import yaml
import zipfile

from toscaparser.utils.gettextutils import _
import toscaparser.utils.yamlparser

YAML_ORDER_PARSER = toscaparser.utils.yamlparser.simple_ordered_parse
log = logging.getLogger('heat-translator')

# Required environment variables to create openstackclient object.
ENV_VARIABLES = ['OS_AUTH_URL', 'OS_PASSWORD', 'OS_USERNAME', 'OS_TENANT_NAME']


class MemoryUnit(object):

    UNIT_SIZE_DEFAULT = 'B'
    UNIT_SIZE_DICT = {'B': 1, 'kB': 1000, 'KiB': 1024, 'MB': 1000000,
                      'MiB': 1048576, 'GB': 1000000000,
                      'GiB': 1073741824, 'TB': 1000000000000,
                      'TiB': 1099511627776}

    @staticmethod
    def convert_unit_size_to_num(size, unit=None):
        """Convert given size to a number representing given unit.

        If unit is None, convert to a number representing UNIT_SIZE_DEFAULT
        :param size: unit size e.g. 1 TB
        :param unit: unit to be converted to e.g GB
        :return: converted number e.g. 1000 for 1 TB size and unit GB
        """
        if unit:
            unit = MemoryUnit.validate_unit(unit)
        else:
            unit = MemoryUnit.UNIT_SIZE_DEFAULT
            log.info(_('A memory unit is not provided for size; using the '
                       'default unit %(default)s.') % {'default': 'B'})
        regex = re.compile(r'(\d*)\s*(\w*)')
        result = regex.match(str(size)).groups()
        if result[1]:
            unit_size = MemoryUnit.validate_unit(result[1])
            converted = int(str_to_num(result[0]) *
                            MemoryUnit.UNIT_SIZE_DICT[unit_size] *
                            math.pow(MemoryUnit.UNIT_SIZE_DICT
                                     [unit], -1))
            log.info(_('Given size %(size)s is converted to %(num)s '
                       '%(unit)s.') % {'size': size,
                     'num': converted, 'unit': unit})
        else:
            converted = (str_to_num(result[0]))
        return converted

    @staticmethod
    def validate_unit(unit):
        if unit in MemoryUnit.UNIT_SIZE_DICT.keys():
            return unit
        else:
            for key in MemoryUnit.UNIT_SIZE_DICT.keys():
                if key.upper() == unit.upper():
                    return key

            msg = _('Provided unit "{0}" is not valid. The valid units are '
                    '{1}').format(unit, MemoryUnit.UNIT_SIZE_DICT.keys())
            log.error(msg)
            raise ValueError(msg)


class CompareUtils(object):

    MISMATCH_VALUE1_LABEL = "<Expected>"
    MISMATCH_VALUE2_LABEL = "<Provided>"
    ORDERLESS_LIST_KEYS = ['allowed_values', 'depends_on']

    @staticmethod
    def compare_dicts(dict1, dict2):
        """Return False if not equal, True if both are equal."""

        if dict1 is None and dict2 is None:
            return True
        if dict1 is None or dict2 is None:
            return False

        both_equal = True
        for dict1_item, dict2_item in zip(dict1.items(), dict2.items()):
            if dict1_item != dict2_item:
                msg = (_("%(label1)s: %(item1)s \n is not equal to \n:"
                         "%(label2)s: %(item2)s")
                       % {'label1': CompareUtils.MISMATCH_VALUE2_LABEL,
                          'item1': dict1_item,
                          'label2': CompareUtils.MISMATCH_VALUE1_LABEL,
                          'item2': dict2_item})
                log.warning(msg)
                both_equal = False
                break
        return both_equal

    @staticmethod
    def compare_hot_yamls(generated_yaml, expected_yaml):
        hot_translated_dict = YAML_ORDER_PARSER(generated_yaml)
        hot_expected_dict = YAML_ORDER_PARSER(expected_yaml)
        return CompareUtils.compare_dicts(hot_translated_dict,
                                          hot_expected_dict)

    @staticmethod
    def reorder(dic):
        '''Canonicalize list items in the dictionary for ease of comparison.

        For properties whose value is a list in which the order does not
        matter, some pre-processing is required to bring those lists into a
        canonical format. We use sorting just to make sure such differences
        in ordering would not cause to a mismatch.
        '''

        if type(dic) is not dict:
            return None

        reordered = {}
        for key in dic.keys():
            value = dic[key]
            if type(value) is dict:
                reordered[key] = CompareUtils.reorder(value)
            elif type(value) is list \
                and key in CompareUtils.ORDERLESS_LIST_KEYS:
                reordered[key] = sorted(value)
            else:
                reordered[key] = value
        return reordered

    @staticmethod
    def diff_dicts(dict1, dict2, reorder=True):
        '''Compares two dictionaries and returns their differences.

        Returns a dictionary of mismatches between the two dictionaries.
        An empty dictionary is returned if two dictionaries are equivalent.
        The reorder parameter indicates whether reordering is required
        before comparison or not.
        '''

        if reorder:
            dict1 = CompareUtils.reorder(dict1)
            dict2 = CompareUtils.reorder(dict2)

        if dict1 is None and dict2 is None:
            return {}
        if dict1 is None or dict2 is None:
            return {CompareUtils.MISMATCH_VALUE1_LABEL: dict1,
                    CompareUtils.MISMATCH_VALUE2_LABEL: dict2}

        diff = {}
        keys1 = set(dict1.keys())
        keys2 = set(dict2.keys())
        for key in keys1.union(keys2):
            if key in keys1 and key not in keys2:
                diff[key] = {CompareUtils.MISMATCH_VALUE1_LABEL: dict1[key],
                             CompareUtils.MISMATCH_VALUE2_LABEL: None}
            elif key not in keys1 and key in keys2:
                diff[key] = {CompareUtils.MISMATCH_VALUE1_LABEL: None,
                             CompareUtils.MISMATCH_VALUE2_LABEL: dict2[key]}
            else:
                val1 = dict1[key]
                val2 = dict2[key]
                if val1 != val2:
                    if type(val1) is dict and type(val2) is dict:
                        diff[key] = CompareUtils.diff_dicts(val1, val2, False)
                    else:
                        diff[key] = {CompareUtils.MISMATCH_VALUE1_LABEL: val1,
                                     CompareUtils.MISMATCH_VALUE2_LABEL: val2}
        return diff


class YamlUtils(object):

    @staticmethod
    def get_dict(yaml_file):
        '''Returns the dictionary representation of the given YAML spec.'''
        try:
            return yaml.safe_load(open(yaml_file))
        except IOError:
            return None

    @staticmethod
    def compare_yamls(yaml1_file, yaml2_file):
        '''Returns true if two dictionaries are equivalent, false otherwise.'''
        dict1 = YamlUtils.get_dict(yaml1_file)
        dict2 = YamlUtils.get_dict(yaml2_file)
        return CompareUtils.compare_dicts(dict1, dict2)

    @staticmethod
    def compare_yaml_dict(yaml_file, dic):
        '''Returns true if yaml matches the dictionary, false otherwise.'''
        return CompareUtils.compare_dicts(YamlUtils.get_dict(yaml_file), dic)


class TranslationUtils(object):

    @staticmethod
    def compare_tosca_translation_with_hot(tosca_file, hot_files, params):
        '''Verify tosca translation against the given hot specification.

        inputs:
        tosca_file: relative local path or URL to the tosca input file
        hot_file: relative path to expected hot output
        params: dictionary of parameter name value pairs

        Returns as a dictionary the difference between the HOT translation
        of the given tosca_file and the given hot_file.
        '''

        from toscaparser.tosca_template import ToscaTemplate
        from translator.hot.tosca_translator import TOSCATranslator

        tosca_tpl = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), tosca_file))
        a_file = os.path.isfile(tosca_tpl)
        if not a_file:
            tosca_tpl = tosca_file

        expected_hot_templates = []
        for hot_file in hot_files:
            expected_hot_templates.append(os.path.join(
                os.path.dirname(os.path.abspath(__file__)), hot_file))

        tosca = ToscaTemplate(tosca_tpl, params, a_file)
        translate = TOSCATranslator(tosca, params)

        basename = os.path.basename(hot_files[0])
        output_hot_templates = translate.translate_to_yaml_files_dict(basename)
        output_dict = {}
        for output_hot_template_name in output_hot_templates:
            output_dict[output_hot_template_name] = \
                toscaparser.utils.yamlparser.simple_parse(
                    output_hot_templates[output_hot_template_name])

        expected_output_dict = {}
        for expected_hot_template in expected_hot_templates:
            expected_output_dict[os.path.basename(expected_hot_template)] = \
                YamlUtils.get_dict(expected_hot_template)

        return CompareUtils.diff_dicts(expected_output_dict, output_dict)


class UrlUtils(object):

    @staticmethod
    def validate_url(path):
        """Validates whether the given path is a URL or not.

        If the given path includes a scheme (http, https, ftp, ...) and a net
        location (a domain name such as www.github.com) it is validated as a
        URL.
        """
        parsed = urlparse(path)
        return bool(parsed.scheme) and bool(parsed.netloc)


def str_to_num(value):
    """Convert a string representation of a number into a numeric type."""
    if isinstance(value, numbers.Number) \
            or isinstance(value, int) \
            or isinstance(value, float):
        return value
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return None


def check_for_env_variables():
    return set(ENV_VARIABLES) < set(os.environ.keys())


def get_ks_access_dict():
    tenant_name = os.getenv('OS_TENANT_NAME')
    username = os.getenv('OS_USERNAME')
    password = os.getenv('OS_PASSWORD')
    auth_url = os.getenv('OS_AUTH_URL')

    auth_dict = {
        "auth": {
            "tenantName": tenant_name,
            "passwordCredentials": {
                "username": username,
                "password": password
            }
        }
    }
    headers = {'Content-Type': 'application/json'}
    try:
        keystone_response = requests.post(auth_url + '/tokens',
                                          data=json.dumps(auth_dict),
                                          headers=headers)
        if keystone_response.status_code != 200:
            return None
        return json.loads(keystone_response.content)
    except Exception:
        return None


def get_url_for(access_dict, service_type):
    if access_dict is None:
        return None
    service_catalog = access_dict['access']['serviceCatalog']
    service_url = ''
    for service in service_catalog:
        if service['type'] == service_type:
            service_url = service['endpoints'][0]['publicURL']
            break
    return service_url


def get_token_id(access_dict):
    if access_dict is None:
        return None
    return access_dict['access']['token']['id']


def decompress(zip_file, dir=None):
    """Decompress Zip file

    Decompress any zip file. For example, TOSCA CSAR

    inputs:
       zip_file: file in zip format
       dir: directory to decompress zip. If not provided an unique temporary
            directory will be generated and used.
    return:
       dir: absolute path to the decopressed directory
    """
    if not dir:
        dir = tempfile.NamedTemporaryFile().name
    with zipfile.ZipFile(zip_file, "r") as zf:
        zf.extractall(dir)
    return dir


def get_dict_value(dict_item, key, get_files):
    if key in dict_item:
        return get_files.append(dict_item[key])
    for k, v in dict_item.items():
        if isinstance(v, dict):
            get_dict_value(v, key, get_files)

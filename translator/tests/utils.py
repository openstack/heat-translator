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

import os


def sample_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__),
                                        '../../samples/'))


def test_sample_root():
    # {heat-translator}/samples/tests
    return os.path.join(sample_root(), 'tests/')


def test_sample_data_root():
    # {heat-translator}/samples/tests/data
    return os.path.join(test_sample_root(), 'data/')


def test_sample(*p):
    return os.path.join(test_sample_data_root(), *p)

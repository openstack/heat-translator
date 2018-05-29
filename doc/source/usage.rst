=====
Usage
=====

Use Heat-Translator with OpenStackClient (OSC)
----------------------------------------------
Assuming that OpenStackClient (OSC) is available in your environment, you can easily install Heat-Translator to use with OSC by following three steps::

    git clone https://github.com/openstack/heat-translator
    cd heat-translator
    sudo python setup.py install

Alternatively, you can install a particular release of Heat-Translator as available at https://pypi.org/project/heat-translator.

Once installation is complete, Heat-Translator is ready to use. The only required argument is ``--template-file``. By default, the ``--template-type`` is set to ``tosca`` which is the
only supported template type at present. Currently you can use Heat-Translator in following three ways.

Translate and get output on command line. For example: ::

    openstack translate template --template-file /home/openstack/heat-translator/translator/tests/data/tosca_helloworld.yaml --template-type tosca

Translate and save output of translated file to a desired destination. For example: ::

    openstack translate template --template-file /home/openstack/heat-translator/translator/tests/data/tosca_helloworld.yaml --template-type tosca --output-file /tmp/hot_hello_world.yaml

Do not translate but only validate template file. For example: ::

    openstack translate template --template-file /home/openstack/heat-translator/translator/tests/data/tosca_helloworld.yaml --template-type tosca --validate-only=true

You can learn more about available options by running following help command::

    openstack help translate template


Use Heat-Translator on its own
------------------------------
Heat-Translator can be used without any specific OpenStack environment set up as below::

    git clone https://github.com/openstack/heat-translator
    python heat_translator.py --template-file==<path to the YAML template> --template-type=<type of template e.g. tosca> --parameters="purpose=test"

The heat_translator.py test program is at the root level of the project. The program has currently tested with TOSCA templates.
The only required argument is ``--template-file``. By default, the ``--template-type`` is set to ``tosca`` which is the only supported template type at present.
The value to the ``--template-file`` is a path to the file that needs to be translated. The file, flat YAML template or CSAR, can be specified as a local file in your
system or via URL.

For example, a TOSCA hello world template can be translated by running the following command from the project location::

    python heat_translator.py --template-file=translator/tests/data/tosca_helloworld.yaml

This should produce a translated Heat Orchestration Template on the command line. The translated content can be saved to a desired file by setting --output-file=<path>.
For example: ::

    python heat_translator.py --template-file=translator/tests/data/tosca_helloworld.yaml --template-type=tosca --output-file=/tmp/hot_helloworld.yaml

An optional argument can be provided to handle user inputs parameters. Also, a template file can only be validated instead of translation by using --validate-only=true
optional argument. The command below shows an example usage::

    python heat_translator.py --template-file=<path to the YAML template> --template-type=<type of template e.g. tosca> --validate-only=true

Alternatively, you can install a particular release of Heat-Translator as available at https://pypi.org/project/heat-translator.
In this case, you can simply run translation via CLI entry point::

    heat-translator --template-file=translator/tests/data/tosca_helloworld.yaml --template-type=tosca

Things To Consider
------------------
* When use Heat-Translator in an OpenStack environment, please ensure that you have one or more preferred flavors and images available in your OpenStack
  environment. To find an appropriate flavor and image, that meets constraints defined in the TOSCA template for the HOST and OS capabilities of TOSCA Compute node,
  the Heat-Translator project first runs a query against Nova flavors and Glance images. During the query call, it uses the metadata of flavors and images.
  If call to Nova or Glance can not be made or no flavor or image is found, the Heat-Translator project will set flavor and image from a pre-defined set of values (as listed in /home/openstack/heat-translator/translator/hot/tosca/tosca_compute.py)
  with the best possible match to the constraints defined in the TOSCA template.
* The ``key_name`` property of Nova server is irrelevant to the TOSCA specification and can not be used in TOSCA template. In order to use it in
  the translated templates, the user must provide it via parameters, and the heat-translator will set it to all resources of ``OS::Nova::Server`` type.
* Since properties of TOSCA Compute OS and HOST capabilities are optional, the user should make sure that either they set these properties correctly
  in the TOSCA template or provide them via CLI parameters in order to find best match of flavor and image.
* The ``flavor`` and ``image`` properties of ``OS::Nova::Server`` resource is irrelevant to the TOSCA specification and can not be used in the TOSCA
  template as such. Heat-Translator sets these properties in the translated template based on constraints defined per TOSCA Compute OS and HOST
  capabilities. However, user may required to use these properties in template in certain circumstances, so in that case, TOSCA Compute can be extended
  with these properties and later used in the node template. For a good example, refer to the ``translator/tests/data/test_tosca_flavor_and_image.yaml`` test
  template.
* The Heat-Translator can be used to automatically deploy translated TOSCA template given that your environment has python-heatclient and python-keystoneclient.
  This can be achieved by providing ``--deploy`` argument to the Heat-Translator. You can provide desired stack name by providing it as ``--stack-name <name>``
  argument. If you do not provide ``--stack-name``, an unique name will be created and used.
  Below is an example command to deploy translated template with a desired stack name::

      heat-translator --template-file translator/tests/data/tosca_helloworld.yaml --stack-name mystack --deploy

* The Heat-Translator supports translation of TOSCA templates to Heat Senlin
  resources (e.g. ``OS::Senlin::Cluster``) but that requires to use a specific
  TOSCA node type called ``tosca.policies.Scaling.Cluster``.
  The ``tosca.policies.Scaling.Cluster`` is a custom type that derives from
  ``tosca.policies.Scaling``. For example usage, refer to the
  ``tosca_cluster_autoscaling.yaml`` and ``hot_cluster_autoscaling.yaml``
  provided under the ``translator/tests/data/autoscaling`` and
  ``translator/tests/data/hot_output/autoscaling`` directories respectively in
  the heat-translator project (``https://github.com/openstack/heat-translator``).
  When you use ``tosca.policies.Scaling`` normative node type, the
  Heat-Translator will translate it to ``OS::Heat::AutoScalingGroup`` Heat
  resource. Related example templates, ``tosca_autoscaling.yaml`` and
  ``hot_autoscaling.yaml`` can be found for reference purposes under the same
  directory structure mentioned above.
* With the version 0.7.0 of Heat-Translator, output of multiple template files
  (for example, nested templates in autoscaling) can be accessed via newly
  introduced API called ``translate_to_yaml_files_dict(<output_filename>)``
  where ``<output_filename>`` is the name of file where you want to store parent
  HOT template. The return value of this API call will be a dictionary in HOT
  YAML with one or multiple file names as keys and translated content as values.
  In order to use this on the command line, simply invoke Heat-Translator with
  ``--output-file`` argument. Here, the parent template will be stored in the
  value specified to the ``--output-file``. Whereas, child templates, if any,
  will be saved at the same location of the parent template.

  Below is an example of how to call the API in your code, where
  ``translator`` is an instance of Heat-Translator::

      yaml_files = translator.translate_to_yaml_files_dict(filename)

  Below is an example of how to use this on the command line::

      heat-translator --template-file translator/tests/data/autoscaling/tosca_autoscaling.yaml --output-file /tmp/hot.yaml

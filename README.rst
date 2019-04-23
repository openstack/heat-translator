========================
Team and repository tags
========================

.. image:: https://governance.openstack.org/tc/badges/heat-translator.svg
    :target: https://governance.openstack.org/tc/reference/tags/index.html

.. Change things from this point on

===============
Heat-Translator
===============

Overview
--------

Heat-Translator is an Openstack project and licensed under Apache 2. It is a
command line tool which takes non-Heat templates as an input and produces a
Heat Orchestration Template (HOT) which can be deployed by Heat. Currently the
development and testing is done with an aim to translate OASIS Topology and
Orchestration Specification for Cloud Applications (TOSCA) templates to
HOT. However, the tool is designed to be easily extended to use with any
format other than TOSCA.

Architecture
------------

Heat-Translator project takes a non-Heat template (e.g. TOSCA flat YAML
template or template embedded in TOSCA Cloud Service Archive (CSAR) format) as
an input, calls an appropriate Parser (e.g. TOSCA Parser) per the type of input
template to parse it and create an in-memory graph, maps it to Heat resources
and then produces a Heat Orchestration Template (HOT) as an output.

How To Use
----------
Please refer to `doc/source/usage.rst <https://github.com/openstack/heat-translator/blob/master/doc/source/usage.rst>`_

Directory Structure
-------------------

Three main directories related to the heat-translator are:

1. hot: It is the generator, that has logic of converting TOSCA in memory graph to HOT YAML files.
2. common: It has all the file that can support the execution of parser and generator.
3. tests: It contains test programs and more importantly several templates which are used for testing.

Project Info
------------

* License: Apache License, Version 2.0
* Documentation: http://docs.openstack.org/heat-translator/
* Bugs and Blueprints: https://storyboard.openstack.org/#!/project/openstack/heat-translator
* Source: http://opendev.org/openstack/heat-translator/
* IRC Channel: #openstack-heat-translator

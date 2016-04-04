#!/usr/bin/env python2

template = """/* AUTOGENERATED, DO NOT EDIT! */
#include <cmocka.h>

{% for _, suiteInit, suiteClean, suiteTests in registry %}
{% if suiteInit and suiteClean %}
extern int {{suiteInit}}(void**);
extern int {{suiteClean}}(void**);
{% endif %}
{% for testName in suiteTests %}
extern void {{testName}}(void**);
{% endfor %}
{% endfor %}

{% for suiteName, suiteInit, suiteClean, suiteTests in registry %}
static const struct CMUnitTest global_test_group_{{suiteName}}[] = {
    {% for testName in suiteTests %}
        cmocka_unit_test({{testName}}),
    {% endfor %}
};
{% endfor %}

struct TestGroup {
    const struct CMUnitTest *tests;
    size_t tests_count;
    CMFixtureFunction setup;
    CMFixtureFunction teardown;
};

static const struct TestGroup global_test_groups[] = {
{% for suiteName, suiteInit, suiteClean, suiteTests in registry %}
    { global_test_group_{{suiteName}},
      {{suiteTests | length}},
      {{suiteInit  | default("NULL", True)}},
      {{suiteClean | default("NULL", True)}} },
{% endfor %}
};
"""

import argparse
import jinja2
import os
import re
import sys

parser = argparse.ArgumentParser(description='Test registry generator for CUnit')
parser.add_argument('--output', metavar='H_FILE',
                    help='header file with generated registry')
parser.add_argument('files', metavar='FILE', nargs='+')

# Will show usage and exit in case arguments cannot be parsed.
arguments = parser.parse_args()

testFiles = []
for fileName in arguments.files:
    if (fileName.endswith('.c') and
        os.path.realpath(fileName) != os.path.realpath(arguments.output)):
           testFiles.append(fileName)

registry = []
for fileName in testFiles:
    baseName   = os.path.basename(fileName)
    suiteName  = os.path.splitext(baseName)[0].replace('-', '_')
    suiteInit  = None
    suiteClean = None
    suiteTests = []
    with open(fileName, mode="r") as f:

        r = re.compile((r"^extern\s+(void|int)\s+(%s_(\w[\w\d]*))\s*\(\s*" +
                        r"void\s+\*\s*\*\s*\w[\w\d]*\)") % suiteName)
        for s in f:
            m = r.match(s)
            if m is None:
                continue

            funcName = m.group(2)
            testName = m.group(3)
             
            if testName == "init":
                suiteInit = funcName
            elif testName == "clean":
                suiteClean = funcName
            else:
                suiteTests.append(funcName)

    if len(suiteTests) == 0:
        continue

    if (suiteInit is None and suiteClean is not None) or \
       (suiteInit is not None and suiteClean is None):
        sys.stderr.write("warning: init and cleanup functions must be both " +
                         "defined or both not\n")
        continue

    registry.append((suiteName, suiteInit, suiteClean, suiteTests))

with open(arguments.output, mode="w") as f:
    e = jinja2.Environment(lstrip_blocks=True, trim_blocks=True)
    t = e.from_string(template)
    f.write(t.render(registry=registry))

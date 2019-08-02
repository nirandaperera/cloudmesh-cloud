###############################################################
# pytest -v --capture=no tests/openstack/openstacktest_compute_openstack.py
# pytest -v  tests/openstack/openstacktest_compute_openstack.py
# pytest -v --capture=no  tests/openstack/openstacktest_compute_openstack.py:Test_compute_openstack.<METHIDNAME>
###############################################################

import pytest
from cloudmesh.common.Shell import Shell
from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.util import HEADING
from cloudmesh.common.variables import Variables
from cloudmesh.common3.Shell import Shell
from cloudmesh.compute.openstack.Provider import Provider
from cloudmesh.config.Config import Config
from cloudmesh.management.configuration.name import Name
from cloudmesh.secgroup.Secgroup import Secgroup
from cloudmesh.secgroup.Secgroup import SecgroupExamples
from cloudmesh.secgroup.Secgroup import SecgroupRule
from cloudmesh.common3.Benchmark import Benchmark

user = Config()["cloudmesh.profile.user"]
variables = Variables()
VERBOSE(variables.dict())

cloud = variables.parameter('cloud')

print("C", cloud)

if cloud != "chameleon":
    raise ValueError("cloud is not chameleon")


def run(label, command):
    result = Shell.run_timed(label, command, service=cloud)
    print(result)
    return result


name_generator = Name(schema=f"{user}-vm", counter=1)

provider = Provider(name=cloud)

rules = SecgroupRule()
groups = Secgroup()
examples = SecgroupExamples()


@pytest.mark.incremental
class TestName:

    def test_load(self):
        HEADING(color="HEADER")

        r = rules.clear()
        g = groups.clear()

        Benchmark.Start()
        examples.load()
        Benchmark.Stop()

        r = rules.list()
        g = groups.list()

        assert len(g) == len(examples.secgroups)
        assert len(r) == len(examples.secrules)

    def test_list_variables(self):
        HEADING()
        Benchmark.Start()
        print(user)
        print(cloud)
        Benchmark.Stop()

    def test_list_secgroups_rules(self):
        HEADING()
        Benchmark.Start()
        groups = provider.list_secgroups()
        Benchmark.Stop()
        provider.Print('json', "secgroup", groups)

    def test_secgroups_delete(self):
        HEADING()
        name = "flask"
        Benchmark.Start()
        r = provider.remove_secgroup(name=name)
        Benchmark.Stop()
        assert r
        g = provider.list_secgroups()
        for e in g:
            print(e['name'])
        provider.Print('table', "secrule", g)

    def test_secgroups_add(self):
        HEADING()
        name = "flask"
        Benchmark.Start()
        provider.add_secgroup(name=name)
        Benchmark.Stop()
        g = provider.list_secgroups(name=name)
        provider.Print('json', "secgroup", g)

        assert len(g) == 1
        assert g[0]['name'] == name

    def test_secgroups_delete_again(self):
        HEADING()
        name = "flask"
        Benchmark.Start()
        r = provider.remove_secgroup(name=name)
        Benchmark.Stop()
        assert r
        g = provider.list_secgroups()
        for e in g:
            print(e['name'])
        provider.Print('table', "secrule", g)

    def test_benchmark(self):
        Benchmark.print()
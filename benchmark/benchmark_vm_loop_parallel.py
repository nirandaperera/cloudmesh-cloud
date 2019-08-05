###############################################################
# pytest -v --capture=no tests/cloud/test_provider_vm06_vm_provider.py
# pytest -v  tests/cloud/test_provider_vm06_vm_provider.py
###############################################################

# TODO: start this with cloud init, e.g, empty mongodb
# TODO: assertuons need to be added

import pytest
from cloudmesh.common.debug import VERBOSE
from cloudmesh.common.util import HEADING
from cloudmesh.common.variables import Variables
from cloudmesh.common3.Benchmark import Benchmark
from cloudmesh.compute.vm.Provider import Provider
from cloudmesh.configuration.Config import Config
from cloudmesh.management.configuration.name import Name
from cloudmesh.common.console import Console
from cloudmesh.common.StopWatch import StopWatch
import time
from multiprocessing import Pool

Benchmark.debug()

user = Config()["cloudmesh.profile.user"]
variables = Variables()
VERBOSE(variables.dict())

cloud = variables.parameter('cloud')

print(f"Test run for {cloud}")

if cloud is None:
    raise ValueError("cloud is not not set")


name_generator = Name()
name_generator.set(f"benchmark-{user}-vm-" + "{counter}")
# name_generator.reset()

name = str(name_generator)

provider = Provider(name=cloud)


def Print():
    data = provider.list()
    print(provider.Print(data=data, output='table', kind='vm'))

current_vms = 0

repeat = 100

batch=3

def generate_names(n):

    names = []
    for i in range(0,n):
        name_generator.incr()
        names.append(str(name_generator))
    return names


def list():
    Print()
    data = provider.list() # update the db


def provider_vm_create(name):
    HEADING()

    try:
        StopWatch.start(f"start {name}")
        parameters = {'name': name}
        data = provider.create(**parameters)
        StopWatch.stop(f"start {name}")

    except Exception as e:
        Console.error(f"could not create VM {name}")
        print (e)

def provider_vm_terminate(name):
    HEADING()
    try:
        StopWatch.start(f"terminate {name}")
        parameters = {'name': name}

        data = provider.destroy(**parameters)
        StopWatch.stop(f"terminate {name}")

    except Exception as e:
        Console.error(f"could not terminate VM {name}")
        print (e)

def create_terrminate(name):
    provider_vm_create(name)
    provider_vm_terminate(name)
    return name

def test_benchmark():
    StopWatch.benchmark(sysinfo=False, csv=False, tag=cloud)


pool = Pool()

p = {}
names = generate_names(20)
results = pool.map(create_terrminate, names)
pool.close()
pool.join()
print (results)


test_benchmark()
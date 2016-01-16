# coding: utf-8

from fabkit import task
from fablib.python import Python


@task
def setup():
    prefix = '/opt/test-python'
    python = Python(prefix)
    python.setup()
    python.install('flake8')
    assert python.get_prefix() == prefix
    assert python.get_cmd() == '{0}/bin/python'.format(prefix)

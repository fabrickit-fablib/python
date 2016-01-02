# coding: utf-8

from fabkit import task
from fablib.python import Python


@task
def setup():
    python = Python('/opt/test-python')
    python.setup()
    python.install('flake8')

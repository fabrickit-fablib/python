# coding: utf-8

import re
from fabric.api import warn_only
from lib.api import package, run, sudo
from fablib import git


def setup():
    """
    easy_install, pipをインストールします。
    また、pipはパッケージインストール時にソースからコンパイルするため、
    いくつかのdevelパッケージをインストールしておきます。
    """

    git.setup()

    package.uninstall('python-crypto')  # デフォルトでインストールされていると邪魔なので消す
    package.install('python-devel')
    package.install('libxml2-devel')
    package.install('libxslt-devel')
    package.install('libffi-devel')
    package.install('postgresql-devel')
    package.install('openssl-devel')
    package.install('gcc')

    with warn_only():
        result = run('which easy_install')
        if result.return_code != 0:
            sudo('wget https://bootstrap.pypa.io/ez_setup.py -O - | sudo python')

        result = run('which pip')
        if result.return_code != 0:
            sudo('easy_install pip')


def pip_show(package_name):
    """
    pip show [package_name] の結果をパースして、タプル形式で返します。
    """

    result = run('pip show {0}'.format(package_name))
    if result == '':
        return None

    RE_NAME = re.compile('Name: (.+)\r')
    RE_VERSION = re.compile('Version: (.+)\r')
    finded_name = RE_NAME.findall(result)
    if len(finded_name) == 0:
        return None

    name = finded_name[0]

    finded_version = RE_VERSION.findall(result)
    if len(finded_version) == 0:
        return None

    version = finded_version[0]
    return (name, version)


def install_from_git(package_name, git_url, tmp_dir=None):
    # encodeがaciiの場合は、utf-8に修正する
    encoding = run('python -c "import sys; print sys.getdefaultencoding()"')
    if encoding == 'ascii':
        site_packages = run('python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"')  # noqa
        sitecustomize = site_packages + '/sitecustomize.py'
        sudo('''echo "import sys
sys.setdefaultencoding(\'utf-8\')" >> {0}'''.format(sitecustomize))

    clone_dir = git.sync(git_url)

    sudo('pip install -r {0}/requirements.txt'.format(clone_dir))

    if not pip_show(package_name):
        sudo('sh -c "cd {0} && python setup.py install"'.format(clone_dir))

# coding: utf-8

import re
from fabkit import api, run, sudo, Package, filer
from fablib import git


def setup(version=None):
    """
    easy_install, pipをインストールします。
    また、pipはパッケージインストール時にソースからコンパイルするため、
    いくつかのdevelパッケージをインストールしておきます。
    """

    git.setup()

    Package('python-crypto').uninstall()  # デフォルトでインストールされていると邪魔なので消す
    Package('python-devel').install()
    Package('libxml2-devel').install()
    Package('libxslt-devel').install()
    Package('libffi-devel').install()
    Package('postgresql-devel').install()
    Package('openssl-devel').install()
    Package('blas-devel').install()
    Package('lapack-devel').install()
    Package('atlas-devel').install()
    Package('gcc').install()
    Package('gcc-gfortran').install()
    Package('wget').install()

    if version is None:
        # XXX pipが一回目でインストールされない
        # 二回目だとインストールされる
        with api.warn_only():
            result = run('which easy_install')
            if result.return_code != 0:
                sudo('wget https://bootstrap.pypa.io/ez_setup.py -O - | sudo python')

            result = run('which pip')
            if result.return_code != 0:
                sudo('easy_install pip')

        # encodeがaciiの場合は、utf-8に修正する
        encoding = run('python -c "import sys; print sys.getdefaultencoding()"')
        if encoding == 'ascii':
            site_packages = run('python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"')  # noqa
            sitecustomize = site_packages + '/sitecustomize.py'
            sudo('''echo "import sys
sys.setdefaultencoding(\'utf-8\')" >> {0}'''.format(sitecustomize))

    elif version is '2.7':
        filer.exists('/tmp/Python-2.7.9')
        run('cd /tmp && wget https://www.python.org/ftp/python/2.7.9/Python-2.7.9.tgz && tar xvf Python-2.7.9.tgz')
        sudo('cd /tmp/Python-2.7.9 && ./configure --prefix=/usr/local && make && make altinstal')


def pip_show(package_name):
    """
    pip show [package_name] の結果をパースして、タプル形式で返します。
    """

    with api.warn_only():
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
    git_dir = git.sync(git_url)

    requirements_txt = '{0}/requirements.txt'.format(git_dir)
    if filer.exists(requirements_txt):
        sudo('pip install -r {0}'.format(requirements_txt))

    if not pip_show(package_name):
        sudo('sh -c "cd {0} && python setup.py install"'.format(git_dir))

    return {
        'git_dir': git_dir,
    }

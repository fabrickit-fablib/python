# coding: utf-8

import re
import os
from fabkit import api, run, sudo, Package, filer, env, user
from fablib import git


class Python():
    def __init__(self, prefix='/usr'):
        self.prefix = prefix

    def get_prefix(self):
        return self.prefix

    def get_cmd(self):
        return '{0}/bin/python'.format(self.prefix)  # noqa

    def setup(self):
        """
        easy_install, pipをインストールします。
        また、pipはパッケージインストール時にソースからコンパイルするため、
        いくつかのdevelパッケージをインストールしておきます。
        """

        git.setup()

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

        with api.warn_only():
            result = run('which easy_install')

        if result.return_code != 0:
            sudo('sh -c "cd /tmp/ && wget https://bootstrap.pypa.io/ez_setup.py -O - | python"')

        with api.warn_only():
            result = run('which pip')

        if result.return_code != 0:
            sudo('easy_install pip')

        if self.prefix != '/usr':
            sudo('pip install virtualenv')
            if not filer.exists(self.prefix):
                sudo('virtualenv {0} --system-site-packages'.format(self.prefix))

    def install(self, package_name=None, file_name=None):
        if package_name:
            sudo("{0}/bin/pip install '{1}'".format(self.prefix, package_name))
        elif file_name:
            sudo("{0}/bin/pip install -r {1}".format(self.prefix, file_name))

    def pip_show(self, package_name):
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

    def install_from_git(self, name, git_url, exec_user='root', branch=None, is_develop=False,
                         mkdirs=[], cpdirs=[], services=[], append_packages=[], **kwargs):

        user.add(exec_user)

        git_dir = os.path.join(self.prefix, 'src', name)
        git.sync(git_url, branch=branch, git_dir=git_dir, owner=env.user)

        requirements_txt = '{0}/requirements.txt'.format(git_dir)
        if filer.exists(requirements_txt):
            self.install(file_name=requirements_txt)

        if is_develop:
            sudo('sh -c "cd {0} && {1}/bin/python setup.py develop"'.format(
                git_dir, self.prefix))
        else:
            sudo('sh -c "cd {0} && {1}/bin/python setup.py install"'.format(
                git_dir, self.prefix))

        for mkdir in mkdirs:
            filer.mkdir(mkdir['path'], owner=mkdir.get('owner', exec_user))

        for cpdir in cpdirs:
            if filer.exists(cpdir['to']):
                continue

            sudo('cp -r {0} {1}'.format(
                os.path.join(git_dir, cpdir['from']), cpdir['to']))

        for service in services:
            service['user'] = exec_user
            filer.template(
                '/etc/systemd/system/{0}.service'.format(service['name']),
                src='systemd.service.j2', mode='755',
                data=service)

        for package in append_packages:
            self.install(package)

        return {
            'git_dir': git_dir,
        }

    def get_site_packages(self):
        return run('{0}/bin/python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"'.format(self.prefix))  # noqa

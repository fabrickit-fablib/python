# coding: utf-8

import re
import os
from fabkit import api, run, sudo, Package, filer, env, user
from fablib import git
from fablit import SimpleBase


class Python(SimpleBase):
    def __init__(self, prefix='/usr'):
        self.prefix = prefix
        self.packages = {
            'CentOS Linux 7.*': [
                'python-devel',
                'libxml2-devel',
                'libxslt-devel',
                'libffi-devel',
                'postgresql-devel',
                'openssl-devel',
                'blas-devel',
                'lapack-devel',
                'atlas-devel',
                'gcc',
                'gcc-gfortran',
                'wget',
            ],
        }

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
        self.init()

        git.setup()
        self.install_packages()

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

    def setup_package(self, name, git_repos=[], exec_user='root', branch=None, is_develop=False,
                      mk_links=[], mk_dirs=[], cp_files=[], services=[], requirements=[], **kwargs):

        user.add(exec_user)

        for git_repo in git_repos:
            git_dir = os.path.join(self.prefix, 'src', git_repo['name'])
            git.sync(git_repo['url'], branch=git_repo['branch'], git_dir=git_dir, owner=env.user)

            requirements_txt = '{0}/requirements.txt'.format(git_dir)
            if filer.exists(requirements_txt):
                self.install(file_name=requirements_txt)

            if is_develop:
                sudo('sh -c "cd {0} && {1}/bin/python setup.py develop"'.format(
                    git_dir, self.prefix))
            else:
                sudo('sh -c "cd {0} && {1}/bin/python setup.py install"'.format(
                    git_dir, self.prefix))

        for mkdir in mk_dirs:
            filer.mkdir(mkdir['path'], owner=mkdir.get('owner', exec_user))

        for cpfile in cp_files:
            if filer.exists(cpfile['dest']):
                continue

            sudo('cp -r {0} {1}'.format(
                os.path.join(git_dir, cpfile['src']), cpfile['dest']))

        for service in services:
            service['user'] = exec_user
            filer.template(
                '/etc/systemd/system/{0}.service'.format(service['name']),
                src='systemd.service.j2', mode='755',
                data=service)

        for requirement in requirements:
            self.install(requirement)

        for link in mk_links:
            if not filer.exists(link['dest']):
                sudo('ln -s {0} {1}'.format(link['src'], link['dest']))

    def get_site_packages(self):
        return run('{0}/bin/python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"'.format(self.prefix))  # noqa

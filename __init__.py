# coding: utf-8

import re
from fabkit import api, run, sudo, Package, filer
from fablib import git


class Python():
    def __init__(self, prefix='/usr', version='2.7'):
        self.prefix = prefix
        self.version = version

    def get_prefix(self):
        return self.prefix

    def get_version(self):
        return self.prefix

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

        if self.prefix != '/usr':
            if self.version == '2.7':
                if not filer.exists('/tmp/Python-2.7.9'):
                    run('cd /tmp && wget https://www.python.org/ftp/python/2.7.9/Python-2.7.9.tgz && tar xvf Python-2.7.9.tgz')  # noqa
                with api.warn_only():
                    result = run('[ -e {0}/bin/python2.7 ]'.format(self.prefix))
                    if result.return_code != 0:
                        sudo('sh -c "cd /tmp/Python-2.7.9 && ./configure --prefix={0} && make && make altinstall"'.format(self.prefix))  # noqa

        with api.warn_only():
            result = run('[ -e {0}/bin/easy_install-{1} ]'.format(self.prefix, self.version))

        if result.return_code != 0:
            sudo('wget https://bootstrap.pypa.io/ez_setup.py -O - | sudo {0}/bin/python{1}'.format(self.prefix, self.version))  # noqa

        with api.warn_only():
            result = run('[ -e {0}/bin/pip{1} ]'.format(self.prefix, self.version))

        if result.return_code != 0:
            sudo('{0}/bin/easy_install-{1} pip'.format(self.prefix, self.version))

    def install(self, package_name=None, file_name=None):
        if package_name:
            sudo("{0}/bin/pip{1} install '{2}'".format(self.prefix, self.version, package_name))
        elif file_name:
            sudo("{0}/bin/pip{1} install -r {2}".format(self.prefix, self.version, file_name))

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

    def install_from_git(self, package_name, git_url, tmp_dir=None):
        git_dir = git.sync(git_url)

        requirements_txt = '{0}/requirements.txt'.format(git_dir)
        if filer.exists(requirements_txt):
            self.install(file_name=requirements_txt)

        if not self.pip_show(package_name):
            sudo('sh -c "cd {0} && {1}/bin/python{2} setup.py install"'.format(
                git_dir, self.prefix, self.version))

        return {
            'git_dir': git_dir,
        }

    def get_site_packages(self):
        return run('{0}/bin/python{1} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"'.format(self.prefix, self.version))  # noqa

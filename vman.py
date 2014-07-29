#!/usr/bin/env python

import os
import subprocess
import tempfile
import posix
import shutil
import sys


class vman():
    def __init__(self, mandir, page, manpages):
        self.mandir = mandir
        self.page = None
        if page:
            self.page = page
        self.manpages = manpages

        self.userid = posix.geteuid()

    def mkdirs(self):
        self.tempdir = tempfile.mkdtemp(prefix='tmp-',
                                        dir='{}/{}'.format(self.mandir,
                                                           self.userid))
        return self.tempdir

    def _getmanpath(self, manpage, page=None):
        cmd = ['man', '-w', manpage]
        if page:
            cmd.insert(2, page)
        return os.path.split(subprocess.check_output(cmd,
                                                     universal_newlines=True))

    def writemans(self):
        self.manfiles = []
        for m in self.manpages:
            p = self._getmanpath(m, self.page)
            manfile = p[1].split('.')
            manfile = '.'.join(manfile[:-1])
            cmd = ['man', '--pager=cat', m]
            if self.page:
                cmd.insert(2, self.page)
            rawman = subprocess.check_output(cmd, env={'MANWIDTH': '77'},
                                             stderr=subprocess.DEVNULL)
            with open('{}/{}'.format(self.tempdir, manfile), 'wb') as fm:
                fm.write(rawman)
            self.manfiles.append(manfile)
        return self.manfiles

    def openmans(self):
        cmd = ['vim', '-n', '-f', '-M']
        manfiles = ['{}/{}'.format(self.tempdir, x) for x in self.manfiles]
        cmd.extend(manfiles)
        subprocess.call(cmd)

    def cleanup(self):
        shutil.rmtree(self.tempdir)

    def main(self):
        try:
            self.mkdirs()
            self.writemans()
            self.openmans()
        except Exception as e:
            print(e)
            #self.cleanup()


if __name__ == '__main__':
    args = sys.argv[1:]
    if args[0] in range(0, 10):
        page = args[0]
        mans = args[1:]
    else:
        page = None
        mans = args
    v = vman('/tmp/manpages', page, mans)
    v.main()

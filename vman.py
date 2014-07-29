#!/usr/bin/env python

import os
import subprocess
import tempfile
import posix
import shutil
import re
import argparse


class vman():
    '''
    vman class
    Main class for opening up man pages in vim.
    Creates a directory structure like so::
        mandir/
               user/
                    tmp-something/
                                  manpage1
                                  manpage2
                                  ...
    Each user gets their own directory in the mandir that only they can work
    with. (700 access on the tmp-something directories)

    To run this as a script you can call vman.main() which will run all of the
    included functions in the correct order, along with cleanup if an exception
    occurs.
    '''
    def __init__(self, mandir, manpages):
        '''
        Arguments:
            mandir (str) -- Directory to store temporary man pages
            manpages (list) -- Manuals to display
        '''
        self.mandir = mandir
        self.manpages = manpages

        self.userid = posix.geteuid()
        self.catcmd = ['man', '--pager=cat']

    def mkdirs(self):
        '''
        Makes temporary directories. Returns the name of the temporary
        directory
        '''
        os.makedirs('{}/{}'.format(self.mandir, self.userid),
                    exist_ok=True,
                    mode=0o700)
        self.tempdir = tempfile.mkdtemp(prefix='tmp-',
                                        dir='{}/{}'.format(self.mandir,
                                                           self.userid))
        return self.tempdir

    def _getmanpaths(self, manpages):
        cmd = ['man', '-w']
        cmd.extend(manpages)
        sp = subprocess.check_output(cmd, universal_newlines=True)
        spl = sp.splitlines()
        return map(os.path.split, spl)

    def _writeman(self, mp):
        manfile = os.path.join(mp[0], mp[1])
        temp = os.path.join(self.tempdir,
                            re.sub(r'\.(gz|bz2|lzo|zip|xz)$', '', mp[1]))
        cmd = self.catcmd.copy()
        cmd.append(manfile)
        raw = subprocess.check_output(cmd, env={'MANWIDTH': '77'},
                                      stderr=subprocess.DEVNULL)
        with open(temp, 'wb') as tf:
            tf.write(raw)
        return temp

    def writemans(self, mps):
        '''
        Writes manfiles to the temporary directory.
        '''
        self.manfiles = []
        for m in mps:
            self.manfiles.append(self._writeman(m))
        return self.manfiles

    def openmans(self):
        '''
        Opens manpages specified in the self.manfiles list.
        '''
        cmd = ['vim', '-n', '-f', '-M']
        cmd.extend(self.manfiles)
        subprocess.call(cmd)

    def cleanup(self):
        '''
        Removes the temporary directory and files.
        '''
        shutil.rmtree(self.tempdir)

    def main(self):
        '''
        Run all of the above in the correct order with cleanup and everything.
        '''
        try:
            self.mkdirs()
            mps = self._getmanpaths(self.manpages)
            self.writemans(mps)
            self.openmans()
            self.cleanup()
        except Exception as e:
            print(e)
            self.cleanup()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        usage='%(prog)s [page] manpage [manpage2 [...]]',
        description='Python utility to open manual pages in vim.')
    parser.add_argument('manpage', nargs='*', help='Man pages to view')
    args = parser.parse_args()
    v = vman('/tmp/manpages', args.manpage)
    v.main()

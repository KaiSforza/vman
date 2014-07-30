#!/usr/bin/env python

import os
import subprocess
import tempfile
import posix
import shutil
import re
import argparse
from multiprocessing import Pool


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

        self.manfiles = list()
        # Command bits. Allows changing the man command or vim command and
        # their arguments.
        self.man = 'man'
        self.vim = 'vim'
        self.manfnd = [self.man, '-w']
        self.catcmd = [self.man, '--encoding=UTF-8', '--pager=cat']

        # Sets some basic vim options:
        # - nonumber: removes numbering regardless of the setting in vimrc
        # - laststatus=2: always show the status bar information
        # - hidden: allow switching buffers without closing them
        # - ft=man: make vim use the man-style highlighting
        self.vimcmd = [self.vim, '-n', '-f', '-M',
                       '-c', 'set nonumber laststatus=2 hidden ft=man']

    def mkdirs(self):
        '''
        Makes temporary directories. Returns the name of the temporary
        directory. Sets the user's directory to 700 if it created the directory
        or chmods the directory to 700 if it exists. The tempfile.mkdtemp()
        function will create a directory with 700 permissions.
        '''
        d = '{}/{}'.format(self.mandir, self.userid)
        os.makedirs(d, exist_ok=True, mode=0o700)
        os.chmod(d, 0o700)
        self.tempdir = tempfile.mkdtemp(prefix='tmp-', dir=d)
        return self.tempdir

    def _getmanpaths(self, manpages):
        cmd = self.manfnd.copy()
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
        with open(temp, 'wb') as tf:
            tf.write(subprocess.check_output(cmd, env={'MANWIDTH': '77'},
                                             stderr=subprocess.DEVNULL))
        return temp

    def writemans(self, mps):
        '''
        Writes manfiles to the temporary directory.
        '''
        with Pool(posix.cpu_count()) as p:
            self.manfiles = p.map(self._writeman, mps)
        return self.manfiles

    def openmans(self):
        '''
        Opens manpages specified in the self.manfiles list.
        '''
        cmd = self.vimcmd.copy()
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
    parser.add_argument('manpage', nargs='+', help='Man pages to view')
    args = parser.parse_args()
    v = vman('/tmp/manpages', args.manpage)
    v.main()

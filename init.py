#!/usr/bin/env python
#
# $Id: $
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

""" Bodhi Initialization """

import os
import sys
import shutil
import turbogears

from os.path import join, isdir, isfile
from bodhi.util import mkmetadatadir
from bodhi.model import Release, Package, Arch, Multilib
from bodhi.deprecated.biarch import biarch

from sqlobject import SQLObjectNotFound
from turbogears import config
from turbogears.database import PackageHub

sys.path.append('/usr/share/createrepo')
import genpkgmetadata

hub = PackageHub("bodhi")
__connection__ = hub


def init_updates_stage():
    """ Initialize the updates-stage """

    stage_dir = config.get('stage_dir')
    print "\nInitializing the staging directory"

    if not isdir(stage_dir):
        os.mkdir(stage_dir)
    if not isdir(join(stage_dir, 'testing')):
        os.mkdir(join(stage_dir, 'testing'))

    for release in Release.select():
        for status in ('', 'testing'):
            stage = join(stage_dir, status, release.repodir)
            mkmetadatadir(join(stage, 'SRPMS'))
            for arch in release.arches:
                mkmetadatadir(join(stage, arch.name))
                mkmetadatadir(join(stage, arch.name, 'debug'))

def import_releases():
    """ Import the releases and multilib  """

    print "\nInitializing Release table and multilib packages..."

    releases = (
        {
            'name'      : 'FC7',
            'long_name' : 'Fedora Core 7',
            'arches'    : map(Arch.byName, ('i386', 'x86_64', 'ppc')),
            'repodir'   : '7'
        },
        {
            'name'      : 'FC6',
            'long_name' : 'Fedora Core 6',
            'arches'    : map(Arch.byName, ('i386', 'x86_64', 'ppc')),
            'repodir'    : '6'
        },
        {
            'name'      : 'FC5',
            'long_name' : 'Fedora Core 5',
            'arches'    : map(Arch.byName, ('i386', 'x86_64', 'ppc')),
            'repodir'   : '5'
        },
        {
            'name'      : 'EPEL5',
            'long_name' : 'EPEL5 Enterprise Extras',
            'arches'    : map(Arch.byName, ('i386', 'x86_64', 'ppc')),
            'repodir'   : 'EPEL5'
        }
    )

    for release in releases:
        num_multilib = 0
        rel = Release(name=release['name'], long_name=release['long_name'],
                      repodir=release['repodir'])
        map(rel.addArch, release['arches'])
        for arch in biarch.keys():
            if not biarch[arch].has_key(release['name'][-1]):
                continue
            for pkg in biarch[arch][release['name'][-1]]:
                try:
                    multilib = Multilib.byPackage(pkg)
                    num_multilib += 1
                except SQLObjectNotFound:
                    multilib = Multilib(package=pkg)
                multilib.addRelease(rel)
                multilib.addArch(Arch.byName(arch))
        print rel
        print " - Added %d multilib packages for %s" % (num_multilib, rel.name)

def import_rebootpkgs():
    """
    Add packages that should suggest a reboot.  Other than these packages, we
    add a package to the database when its first update is added to the system
    """
    for pkg in config.get('reboot_pkgs').split():
        Package(name=pkg, suggest_reboot=True)

def init_arches():
    """ Initialize the arch tables """
    arches = {
            # arch        subarches
            'i386'      : ['i386', 'i486', 'i586', 'i686', 'athlon', 'noarch'],
            'x86_64'    : ['x86_64', 'ia32e', 'noarch'],
            'ppc'       : ['ppc', 'noarch']
    }

    biarches = {
            # arch        compatarches
            'i386'      : [],
            'x86_64'    : ['i386', 'i486', 'i586', 'i686', 'athlon'],
            'ppc'       : ['ppc64', 'ppc64iseries']
    }

    print "Initializing Arch tables..."
    for arch in arches.keys():
        a = Arch(name=arch, subarches=arches[arch], compatarches=biarches[arch])
        print a

def clean_tables():
    Release.dropTable(ifExists=True, cascade=True)
    Package.dropTable(ifExists=True, cascade=True)
    Arch.dropTable(ifExists=True, cascade=True)
    Multilib.dropTable(ifExists=True, cascade=True)
    hub.commit()
    Release.createTable(ifNotExists=True)
    Package.createTable(ifNotExists=True)
    Arch.createTable(ifNotExists=True)
    Multilib.createTable(ifNotExists=True)

def load_config():
    """ Load the appropriate configuration so we can get at the values """
    configfile = 'dev.cfg'
    if not isfile(configfile):
        configfile = 'prod.cfg'
    turbogears.update_config(configfile=configfile,
                             modulename='bodhi.config')

##
## Initialize the package/release/multilib tables
##
if __name__ == '__main__':
    load_config()
    hub.begin()
    clean_tables()
    init_arches()
    import_releases()
    import_rebootpkgs()
    init_updates_stage()
    hub.commit()

#!/usr/bin/python
# encoding: utf-8
#
# Copyright 2017 Greg Neagle.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''A tool to make bootable disk volumes from the output of autonbi. Especially
useful to make bootable disks containing Imagr and the 'SIP-ignoring' kernel,
which allows Imagr to run scripts that affect SIP state, set UAKEL options, and
run the `startosinstall` component, all of which might otherwise require network
booting from a NetInstall-style nbi.'''

import argparse
import os
import plistlib
import subprocess
import sys
import urlparse


# dmg helpers
def mountdmg(dmgpath):
    """
    Attempts to mount the dmg at dmgpath and returns first mountpoint
    """
    mountpoints = []
    dmgname = os.path.basename(dmgpath)
    cmd = ['/usr/bin/hdiutil', 'attach', dmgpath,
           '-mountRandom', '/tmp', '-nobrowse', '-plist',
           '-owners', 'on']
    proc = subprocess.Popen(cmd, bufsize=-1,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (pliststr, err) = proc.communicate()
    if proc.returncode:
        print >> sys.stderr, 'Error: "%s" while mounting %s.' % (err, dmgname)
        return None
    if pliststr:
        plist = plistlib.readPlistFromString(pliststr)
        for entity in plist['system-entities']:
            if 'mount-point' in entity:
                mountpoints.append(entity['mount-point'])

    return mountpoints[0]


def unmountdmg(mountpoint):
    """
    Unmounts the dmg at mountpoint
    """
    proc = subprocess.Popen(['/usr/bin/hdiutil', 'detach', mountpoint],
                            bufsize=-1, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    (dummy_output, err) = proc.communicate()
    if proc.returncode:
        print >> sys.stderr, 'Polite unmount failed: %s' % err
        print >> sys.stderr, 'Attempting to force unmount %s' % mountpoint
        # try forcing the unmount
        retcode = subprocess.call(['/usr/bin/hdiutil', 'detach', mountpoint,
                                   '-force'])
        if retcode:
            print >> sys.stderr, 'Failed to unmount %s' % mountpoint


def locate_basesystem_dmg(nbi):
    '''Finds and returns the relative path to the BaseSystem.dmg within the
    NetInstall.dmg'''
    source_boot_plist = os.path.join(nbi, 'i386/com.apple.Boot.plist')
    try:
        boot_args = plistlib.readPlist(source_boot_plist)
    except Exception, err:
        print >> sys.stderr, err
        sys.exit(-1)
    kernel_flags = boot_args.get('Kernel Flags')
    if not kernel_flags:
        print >> sys.stderr, 'i386/com.apple.Boot.plist is missing Kernel Flags'
        sys.exit(-1)
    # kernel flags should in the form 'root-dmg=file:///path'
    if not kernel_flags.startswith('root-dmg='):
        print >> sys.stderr, 'Unexpected Kernel Flags: %s' % kernel_flags
        sys.exit(-1)
    file_url = kernel_flags[9:]
    dmg_path = urlparse.unquote(urlparse.urlparse(file_url).path)
    # return path minus leading slash
    return dmg_path.lstrip('/')


def copy_system_version_plist(nbi, target_volume):
    '''Copies System/Library/CoreServices/SystemVersion.plist from the
    BaseSystem.dmg to the target volume.'''
    netinstall_dmg = os.path.join(nbi, 'NetInstall.dmg')
    if not os.path.exists(netinstall_dmg):
        print >> sys.stderr, "Missing NetInstall.dmg from nbi folder"
        sys.exit(-1)
    print 'Mounting %s...' % netinstall_dmg
    netinstall_mount = mountdmg(netinstall_dmg)
    if not netinstall_mount:
        sys.exit(-1)
    basesystem_dmg = os.path.join(netinstall_mount, locate_basesystem_dmg(nbi))
    print 'Mounting %s...' % basesystem_dmg
    basesystem_mount = mountdmg(basesystem_dmg)
    if not basesystem_mount:
        unmountdmg(netinstall_mount)
        sys.exit(-1)
    source = os.path.join(
        basesystem_mount, 'System/Library/CoreServices/SystemVersion.plist')
    dest = os.path.join(
        target_volume, 'System/Library/CoreServices/SystemVersion.plist')
    try:
        subprocess.check_call(
            ['/usr/bin/ditto', '-V', source, dest])
    except subprocess.CalledProcessError, err:
        print >> sys.stderr, err
        unmountdmg(basesystem_mount)
        unmountdmg(netinstall_mount)
        sys.exit(-1)

    unmountdmg(basesystem_mount)
    unmountdmg(netinstall_mount)


def copy_boot_files(nbi, target_volume):
    '''Copies some boot files, yo'''
    files_to_copy = [
        ['NetInstall.dmg', 'NetInstall.dmg'],
        ['i386/PlatformSupport.plist',
         'System/Library/CoreServices/PlatformSupport.plist'],
        ['i386/booter', 'System/Library/CoreServices/boot.efi'],
        ['i386/booter', 'usr/standalone/i386/boot.efi'],
        ['i386/x86_64/kernelcache',
         'System/Library/PrelinkedKernels/prelinkedkernel']
    ]
    for source, dest in files_to_copy:
        full_source = os.path.join(nbi, source)
        full_dest = os.path.join(target_volume, dest)
        try:
            subprocess.check_call(
                ['/usr/bin/ditto', '-V', full_source, full_dest])
        except subprocess.CalledProcessError, err:
            print >> sys.stderr, err
            sys.exit(-1)


def make_boot_plist(nbi, target_volume):
    '''Creates our com.apple.Boot.plist'''
    source_boot_plist = os.path.join(nbi, 'i386/com.apple.Boot.plist')
    try:
        boot_args = plistlib.readPlist(source_boot_plist)
    except Exception, err:
        print >> sys.stderr, err
        sys.exit(-1)
    kernel_flags = boot_args.get('Kernel Flags')
    if not kernel_flags:
        print >> sys.stderr, 'i386/com.apple.Boot.plist is missing Kernel Flags'
        sys.exit(-1)
    # prepend the container-dmg path
    boot_args['Kernel Flags'] = (
        'container-dmg=file:///NetInstall.dmg ' + kernel_flags)
    boot_plist = os.path.join(
        target_volume,
        'Library/Preferences/SystemConfiguration/com.apple.Boot.plist')
    plist_dir = os.path.dirname(boot_plist)
    if not os.path.exists(plist_dir):
        os.makedirs(plist_dir)
    try:
        plistlib.writePlist(boot_args, boot_plist)
    except Exception, err:
        print >> sys.stderr, err
        sys.exit(-1)


def bless(target_volume, label=None):
    '''Bless the target volume'''
    blessfolder = os.path.join(target_volume, 'System/Library/CoreServices')
    if not label:
        label = os.path.basename(target_volume)
    try:
        subprocess.check_call(
            ['/usr/sbin/bless', '--folder', blessfolder, '--label', label])
    except subprocess.CalledProcessError, err:
        print >> sys.stderr, err
        sys.exit(-1)


def main():
    '''Do the thing we were made for'''
    parser = argparse.ArgumentParser()
    parser.add_argument('--nbi', required=True, metavar='path_to_nbi',
                        help='Path to nbi folder created by autonbi.')
    parser.add_argument('--volume', required=True, 
                        metavar='path_to_disk_volume',
                        help='Path to disk volume.')
    args = parser.parse_args()
    copy_system_version_plist(args.nbi, args.volume)
    copy_boot_files(args.nbi, args.volume)
    make_boot_plist(args.nbi, args.volume)
    bless(args.volume)


if __name__ == '__main__':
    main()

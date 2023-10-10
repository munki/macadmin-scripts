#!/usr/bin/env python
# encoding: utf-8
#
# Copyright 2017-2022 Greg Neagle.
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
#
# Thanks to Tim Sutton for ideas, suggestions, and sample code.
#

'''installinstallmacos.py
A tool to download the parts for an Install macOS app from Apple's
softwareupdate servers and install a functioning Install macOS app onto an
empty disk image'''

# Python 3 compatibility shims
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import argparse
import gzip
import os
import plistlib
import subprocess
import sys
try:
    # python 2
    from urllib.parse import urlsplit
except ImportError:
    # python 3
    from urlparse import urlsplit
from xml.dom import minidom
from xml.parsers.expat import ExpatError

try:
    import xattr
except ImportError:
    print("This tool requires the Python xattr module. "
          "Perhaps run `pip install xattr` to install it.")
    sys.exit(-1)


DEFAULT_SUCATALOGS = {
    '17': 'https://swscan.apple.com/content/catalogs/others/'
          'index-10.13-10.12-10.11-10.10-10.9'
          '-mountainlion-lion-snowleopard-leopard.merged-1.sucatalog',
    '18': 'https://swscan.apple.com/content/catalogs/others/'
          'index-10.14-10.13-10.12-10.11-10.10-10.9'
          '-mountainlion-lion-snowleopard-leopard.merged-1.sucatalog',
    '19': 'https://swscan.apple.com/content/catalogs/others/'
          'index-10.15-10.14-10.13-10.12-10.11-10.10-10.9'
          '-mountainlion-lion-snowleopard-leopard.merged-1.sucatalog',
    '20': 'https://swscan.apple.com/content/catalogs/others/'
          'index-10.16-10.15-10.14-10.13-10.12-10.11-10.10-10.9'
          '-mountainlion-lion-snowleopard-leopard.merged-1.sucatalog',
    '21': 'https://swscan.apple.com/content/catalogs/others/'
          'index-12-10.16-10.15-10.14-10.13-10.12-10.11-10.10-10.9'
          '-mountainlion-lion-snowleopard-leopard.merged-1.sucatalog',
    '22': 'https://swscan.apple.com/content/catalogs/others/'
          'index-13-12-10.16-10.15-10.14-10.13-10.12-10.11-10.10-10.9'
          '-mountainlion-lion-snowleopard-leopard.merged-1.sucatalog',
    '23': 'https://swscan.apple.com/content/catalogs/others/'
          'index-14-13-12-10.16-10.15-10.14-10.13-10.12-10.11-10.10-10.9'
          '-mountainlion-lion-snowleopard-leopard.merged-1.sucatalog'
}

SEED_CATALOGS_PLIST = (
    '/System/Library/PrivateFrameworks/Seeding.framework/Versions/Current/'
    'Resources/SeedCatalogs.plist'
)


def get_input(prompt=None):
    '''Python 2 and 3 wrapper for raw_input/input'''
    try:
        return raw_input(prompt)
    except NameError:
        # raw_input doesn't exist in Python 3
        return input(prompt)


def read_plist(filepath):
    '''Wrapper for the differences between Python 2 and Python 3's plistlib'''
    try:
        with open(filepath, "rb") as fileobj:
            return plistlib.load(fileobj)
    except AttributeError:
        # plistlib module doesn't have a load function (as in Python 2)
        return plistlib.readPlist(filepath)


def read_plist_from_string(bytestring):
    '''Wrapper for the differences between Python 2 and Python 3's plistlib'''
    try:
        return plistlib.loads(bytestring)
    except AttributeError:
        # plistlib module doesn't have a load function (as in Python 2)
        return plistlib.readPlistFromString(bytestring)


def get_seeding_program(sucatalog_url):
    '''Returns a seeding program name based on the sucatalog_url'''
    try:
        seed_catalogs = read_plist(SEED_CATALOGS_PLIST)
        for key, value in seed_catalogs.items():
            if sucatalog_url == value:
                return key
        return ''
    except (OSError, IOError, ExpatError, AttributeError, KeyError) as err:
        print(err, file=sys.stderr)
        return ''


def get_seed_catalog(seedname='DeveloperSeed'):
    '''Returns the developer seed sucatalog'''
    try:
        seed_catalogs = read_plist(SEED_CATALOGS_PLIST)
        return seed_catalogs.get(seedname)
    except (OSError, IOError, ExpatError, AttributeError, KeyError) as err:
        print(err, file=sys.stderr)
        return ''


def get_seeding_programs():
    '''Returns the list of seeding program names'''
    try:
        seed_catalogs = read_plist(SEED_CATALOGS_PLIST)
        return list(seed_catalogs.keys())
    except (OSError, IOError, ExpatError, AttributeError, KeyError) as err:
        print(err, file=sys.stderr)
        return ''


def get_default_catalog():
    '''Returns the default softwareupdate catalog for the current OS'''
    darwin_major = os.uname()[2].split('.')[0]
    return DEFAULT_SUCATALOGS.get(darwin_major)


def make_sparse_image(volume_name, output_path):
    '''Make a sparse disk image we can install a product to'''
    cmd = ['/usr/bin/hdiutil', 'create', '-size', '16g', '-fs', 'HFS+',
           '-volname', volume_name, '-type', 'SPARSE', '-plist', output_path]
    try:
        output = subprocess.check_output(cmd)
    except subprocess.CalledProcessError as err:
        print(err, file=sys.stderr)
        exit(-1)
    try:
        return read_plist_from_string(output)[0]
    except IndexError as err:
        print('Unexpected output from hdiutil: %s' % output, file=sys.stderr)
        exit(-1)
    except ExpatError as err:
        print('Malformed output from hdiutil: %s' % output, file=sys.stderr)
        print(err, file=sys.stderr)
        exit(-1)


def make_compressed_dmg(app_path, diskimagepath):
    """Returns path to newly-created compressed r/o disk image containing
    Install macOS.app"""

    print('Making read-only compressed disk image containing %s...'
          % os.path.basename(app_path))
    cmd = ['/usr/bin/hdiutil', 'create', '-fs', 'HFS+',
           '-srcfolder', app_path, diskimagepath]
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as err:
        print(err, file=sys.stderr)
    else:
        print('Disk image created at: %s' % diskimagepath)


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
        print('Error: "%s" while mounting %s.' % (err, dmgname),
              file=sys.stderr)
        return None
    if pliststr:
        plist = read_plist_from_string(pliststr)
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
        print('Polite unmount failed: %s' % err, file=sys.stderr)
        print('Attempting to force unmount %s' % mountpoint, file=sys.stderr)
        # try forcing the unmount
        retcode = subprocess.call(['/usr/bin/hdiutil', 'detach', mountpoint,
                                   '-force'])
        if retcode:
            print('Failed to unmount %s' % mountpoint, file=sys.stderr)


def install_product(dist_path, target_vol):
    '''Install a product to a target volume.
    Returns a boolean to indicate success or failure.'''
    # set CM_BUILD env var to make Installer bypass eligibilty checks
    # when installing packages (for machine-specific OS builds)
    os.environ["CM_BUILD"] = "CM_BUILD"
    cmd = ['/usr/sbin/installer', '-pkg', dist_path, '-target', target_vol]
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as err:
        print(err, file=sys.stderr)
        return False
    else:
        # Apple postinstall script bug ends up copying files to a path like
        # /tmp/dmg.T9ak1HApplications
        path = target_vol + 'Applications'
        if os.path.exists(path):
            print('*********************************************************')
            print('*** Working around a very dumb Apple bug in a package ***')
            print('*** postinstall script that fails to correctly target ***')
            print('*** the Install macOS.app when installed to a volume  ***')
            print('*** other than the current boot volume.               ***')
            print('***       Please file feedback with Apple!            ***')
            print('*********************************************************')
            subprocess.check_call(
                ['/usr/bin/ditto',
                 path,
                 os.path.join(target_vol, 'Applications')]
            )
            subprocess.check_call(['/bin/rm', '-r', path])
        return True

class ReplicationError(Exception):
    '''A custom error when replication fails'''
    pass


def replicate_url(full_url,
                  root_dir='/tmp',
                  show_progress=False,
                  ignore_cache=False,
                  attempt_resume=False):
    '''Downloads a URL and stores it in the same relative path on our
    filesystem. Returns a path to the replicated file.'''

    path = urlsplit(full_url)[2]
    relative_url = path.lstrip('/')
    relative_url = os.path.normpath(relative_url)
    local_file_path = os.path.join(root_dir, relative_url)
    if show_progress:
        options = '-fL'
    else:
        options = '-sfL'
    need_download = True
    while need_download:
        curl_cmd = ['/usr/bin/curl', options,
                    '--create-dirs',
                    '-o', local_file_path,
                    '-w', '%{http_code}']
        if not full_url.endswith(".gz"):
            # stupid hack for stupid Apple behavior where it sometimes returns
            # compressed files even when not asked for
            curl_cmd.append('--compressed')
        resumed = False
        if not ignore_cache and os.path.exists(local_file_path):
            if not attempt_resume:
                curl_cmd.extend(['-z', local_file_path])
            else:
                resumed = True
                curl_cmd.extend(['-z', '-' + local_file_path, '-C', '-'])
        curl_cmd.append(full_url)
        print("Downloading %s..." % full_url)
        need_download = False
        try:
            output = subprocess.check_output(curl_cmd)
        except subprocess.CalledProcessError as err:
            if not resumed or not err.output.isdigit():
                raise ReplicationError(err)
            # HTTP error 416 on resume: the download is already complete and the
            # file is up-to-date
            # HTTP error 412 on resume: the file was updated server-side
            if int(err.output) == 412:
                print("Removing %s and retrying." % local_file_path)
                os.unlink(local_file_path)
                need_download = True
            elif int(err.output) != 416:
                raise ReplicationError(err)
    return local_file_path


def parse_server_metadata(filename):
    '''Parses a softwareupdate server metadata file, looking for information
    of interest.
    Returns a dictionary containing title, version, and description.'''
    title = ''
    vers = ''
    try:
        md_plist = read_plist(filename)
    except (OSError, IOError, ExpatError) as err:
        print('Error reading %s: %s' % (filename, err), file=sys.stderr)
        return {}
    vers = md_plist.get('CFBundleShortVersionString', '')
    localization = md_plist.get('localization', {})
    preferred_localization = (localization.get('English') or
                              localization.get('en'))
    if preferred_localization:
        title = preferred_localization.get('title', '')

    metadata = {}
    metadata['title'] = title
    metadata['version'] = vers
    return metadata


def get_server_metadata(catalog, product_key, workdir, ignore_cache=False):
    '''Replicate ServerMetaData'''
    try:
        url = catalog['Products'][product_key]['ServerMetadataURL']
        try:
            smd_path = replicate_url(
                url, root_dir=workdir, ignore_cache=ignore_cache)
            return smd_path
        except ReplicationError as err:
            print('Could not replicate %s: %s' % (url, err), file=sys.stderr)
            return None
    except KeyError:
        #print('Malformed catalog.', file=sys.stderr)
        return None


def parse_dist(filename):
    '''Parses a softwareupdate dist file, returning a dict of info of
    interest'''
    dist_info = {}
    try:
        dom = minidom.parse(filename)
    except ExpatError:
        print('Invalid XML in %s' % filename, file=sys.stderr)
        return dist_info
    except IOError as err:
        print('Error reading %s: %s' % (filename, err), file=sys.stderr)
        return dist_info

    titles = dom.getElementsByTagName('title')
    if titles:
        dist_info['title_from_dist'] = titles[0].firstChild.wholeText

    auxinfos = dom.getElementsByTagName('auxinfo')
    if not auxinfos:
        return dist_info
    auxinfo = auxinfos[0]
    key = None
    value = None
    children = auxinfo.childNodes
    # handle the possibility that keys from auxinfo may be nested
    # within a 'dict' element
    dict_nodes = [n for n in auxinfo.childNodes
                  if n.nodeType == n.ELEMENT_NODE and
                  n.tagName == 'dict']
    if dict_nodes:
        children = dict_nodes[0].childNodes
    for node in children:
        if node.nodeType == node.ELEMENT_NODE and node.tagName == 'key':
            key = node.firstChild.wholeText
        if node.nodeType == node.ELEMENT_NODE and node.tagName == 'string':
            value = node.firstChild.wholeText
        if key and value:
            dist_info[key] = value
            key = None
            value = None
    return dist_info


def download_and_parse_sucatalog(sucatalog, workdir, ignore_cache=False):
    '''Downloads and returns a parsed softwareupdate catalog'''
    try:
        localcatalogpath = replicate_url(
            sucatalog, root_dir=workdir, ignore_cache=ignore_cache)
    except ReplicationError as err:
        print('Could not replicate %s: %s' % (sucatalog, err), file=sys.stderr)
        exit(-1)
    if os.path.splitext(localcatalogpath)[1] == '.gz':
        with gzip.open(localcatalogpath) as the_file:
            content = the_file.read()
            try:
                catalog = read_plist_from_string(content)
                return catalog
            except ExpatError as err:
                print('Error reading %s: %s' % (localcatalogpath, err),
                      file=sys.stderr)
                exit(-1)
    else:
        try:
            catalog = read_plist(localcatalogpath)
            return catalog
        except (OSError, IOError, ExpatError) as err:
            print('Error reading %s: %s' % (localcatalogpath, err),
                  file=sys.stderr)
            exit(-1)


def find_mac_os_installers(catalog):
    '''Return a list of product identifiers for what appear to be macOS
    installers'''
    mac_os_installer_products = []
    if 'Products' in catalog:
        for product_key in catalog['Products'].keys():
            product = catalog['Products'][product_key]
            try:
                if product['ExtendedMetaInfo'][
                        'InstallAssistantPackageIdentifiers']:
                    mac_os_installer_products.append(product_key)
            except KeyError:
                continue
    return mac_os_installer_products


def os_installer_product_info(catalog, workdir, ignore_cache=False):
    '''Returns a dict of info about products that look like macOS installers'''
    product_info = {}
    installer_products = find_mac_os_installers(catalog)
    for product_key in installer_products:
        product_info[product_key] = {}
        filename = get_server_metadata(catalog, product_key, workdir)
        if filename:
            product_info[product_key] = parse_server_metadata(filename)
        else:
            print('No server metadata for %s' % product_key)
            product_info[product_key]['title'] = None
            product_info[product_key]['version'] = None

        product = catalog['Products'][product_key]
        product_info[product_key]['PostDate'] = product['PostDate']
        distributions = product['Distributions']
        dist_url = distributions.get('English') or distributions.get('en')
        try:
            dist_path = replicate_url(
                dist_url, root_dir=workdir, ignore_cache=ignore_cache)
        except ReplicationError as err:
            print('Could not replicate %s: %s' % (dist_url, err),
                  file=sys.stderr)
        else:
            dist_info = parse_dist(dist_path)
            product_info[product_key]['DistributionPath'] = dist_path
            product_info[product_key].update(dist_info)
            if not product_info[product_key]['title']:
                product_info[product_key]['title'] = dist_info.get('title_from_dist')
            if not product_info[product_key]['version']:
                product_info[product_key]['version'] = dist_info.get('VERSION')
        
    return product_info


def replicate_product(catalog, product_id, workdir, ignore_cache=False):
    '''Downloads all the packages for a product'''
    product = catalog['Products'][product_id]
    for package in product.get('Packages', []):
        # TO-DO: Check 'Size' attribute and make sure
        # we have enough space on the target
        # filesystem before attempting to download
        if 'URL' in package:
            try:
                replicate_url(
                    package['URL'], root_dir=workdir,
                    show_progress=True, ignore_cache=ignore_cache,
                    attempt_resume=(not ignore_cache))
            except ReplicationError as err:
                print('Could not replicate %s: %s' % (package['URL'], err),
                      file=sys.stderr)
                exit(-1)
        if 'MetadataURL' in package:
            try:
                replicate_url(package['MetadataURL'], root_dir=workdir,
                              ignore_cache=ignore_cache)
            except ReplicationError as err:
                print('Could not replicate %s: %s'
                      % (package['MetadataURL'], err), file=sys.stderr)
                exit(-1)


def find_installer_app(mountpoint):
    '''Returns the path to the Install macOS app on the mountpoint'''
    applications_dir = os.path.join(mountpoint, 'Applications')
    for item in os.listdir(applications_dir):
        if item.endswith('.app'):
            return os.path.join(applications_dir, item)
    return None


def main():
    '''Do the main thing here'''
    parser = argparse.ArgumentParser()
    parser.add_argument('--seedprogram', default='',
                        help='Which Seed Program catalog to use. Valid values '
                        'are %s.' % ', '.join(get_seeding_programs()))
    parser.add_argument('--catalogurl', default='',
                        help='Software Update catalog URL. This option '
                        'overrides any seedprogram option.')
    parser.add_argument('--workdir', metavar='path_to_working_dir',
                        default='.',
                        help='Path to working directory on a volume with over '
                        '10G of available space. Defaults to current working '
                        'directory.')
    parser.add_argument('--compress', action='store_true',
                        help='Output a read-only compressed disk image with '
                        'the Install macOS app at the root. This is now the '
                        'default. Use --raw to get a read-write sparse image '
                        'with the app in the Applications directory.')
    parser.add_argument('--raw', action='store_true',
                        help='Output a read-write sparse image '
                        'with the app in the Applications directory. Requires '
                        'less available disk space and is faster.')
    parser.add_argument('--ignore-cache', action='store_true',
                        help='Ignore any previously cached files.')
    args = parser.parse_args()

    if os.getuid() != 0:
        sys.exit('This command requires root (to install packages), so please '
                 'run again with sudo or as root.')

    current_dir = os.getcwd()
    if os.path.expanduser("~") in current_dir:
        bad_dirs = ['Documents', 'Desktop', 'Downloads', 'Library']
        for bad_dir in bad_dirs:
            if bad_dir in os.path.split(current_dir):
                print('Running this script from %s may not work as expected. '
                      'If this does not run as expected, please run again from '
                      'somewhere else, such as /Users/Shared.'
                      % current_dir, file=sys.stderr)

    if args.catalogurl:
        su_catalog_url = args.catalogurl
    elif args.seedprogram:
        su_catalog_url = get_seed_catalog(args.seedprogram)
        if not su_catalog_url:
            print('Could not find a catalog url for seed program %s'
                  % args.seedprogram, file=sys.stderr)
            print('Valid seeding programs are: %s'
                  % ', '.join(get_seeding_programs()), file=sys.stderr)
            exit(-1)
    else:
        su_catalog_url = get_default_catalog()
        if not su_catalog_url:
            print('Could not find a default catalog url for this OS version.',
                  file=sys.stderr)
            exit(-1)

    # download sucatalog and look for products that are for macOS installers
    catalog = download_and_parse_sucatalog(
        su_catalog_url, args.workdir, ignore_cache=args.ignore_cache)
    product_info = os_installer_product_info(
        catalog, args.workdir, ignore_cache=args.ignore_cache)

    if not product_info:
        print('No macOS installer products found in the sucatalog.',
              file=sys.stderr)
        exit(-1)

    # display a menu of choices (some seed catalogs have multiple installers)
    print('%2s %14s %10s %8s %11s  %s'
          % ('#', 'ProductID', 'Version', 'Build', 'Post Date', 'Title'))
    for index, product_id in enumerate(product_info):
        print('%2s %14s %10s %8s %11s  %s' % (
            index + 1,
            product_id,
            product_info[product_id].get('version', 'UNKNOWN'),
            product_info[product_id].get('BUILD', 'UNKNOWN'),
            product_info[product_id]['PostDate'].strftime('%Y-%m-%d'),
            product_info[product_id]['title']
        ))

    answer = get_input(
        '\nChoose a product to download (1-%s): ' % len(product_info))
    try:
        index = int(answer) - 1
        if index < 0:
            raise ValueError
        product_id = list(product_info.keys())[index]
    except (ValueError, IndexError):
        print('Exiting.')
        exit(0)

    # download all the packages for the selected product
    replicate_product(
        catalog, product_id, args.workdir, ignore_cache=args.ignore_cache)

    # generate a name for the sparseimage
    volname = ('Install_macOS_%s-%s'
               % (product_info[product_id]['version'],
                  product_info[product_id]['BUILD']))
    sparse_diskimage_path = os.path.join(args.workdir, volname + '.sparseimage')
    if os.path.exists(sparse_diskimage_path):
        os.unlink(sparse_diskimage_path)

    # make an empty sparseimage and mount it
    print('Making empty sparseimage...')
    sparse_diskimage_path = make_sparse_image(volname, sparse_diskimage_path)
    mountpoint = mountdmg(sparse_diskimage_path)
    if mountpoint:
        # install the product to the mounted sparseimage volume
        success = install_product(
            product_info[product_id]['DistributionPath'],
            mountpoint)
        if not success:
            print('Product installation failed.', file=sys.stderr)
            unmountdmg(mountpoint)
            exit(-1)
        # add the seeding program xattr to the app if applicable
        seeding_program = get_seeding_program(su_catalog_url)
        if seeding_program:
            installer_app = find_installer_app(mountpoint)
            if installer_app:
                print("Adding seeding program %s extended attribute to app"
                      % seeding_program)
                xattr.setxattr(installer_app, 'SeedProgram',
                               seeding_program.encode("UTF-8"))
        print('Product downloaded and installed to %s' % sparse_diskimage_path)
        if args.raw:
            unmountdmg(mountpoint)
        else:
            # if --raw option not given, create a r/o compressed diskimage
            # containing the Install macOS app
            compressed_diskimagepath = os.path.join(
                args.workdir, volname + '.dmg')
            if os.path.exists(compressed_diskimagepath):
                os.unlink(compressed_diskimagepath)
            app_path = find_installer_app(mountpoint)
            if app_path:
                make_compressed_dmg(app_path, compressed_diskimagepath)
            # unmount sparseimage
            unmountdmg(mountpoint)
            # delete sparseimage since we don't need it any longer
            os.unlink(sparse_diskimage_path)


if __name__ == '__main__':
    main()

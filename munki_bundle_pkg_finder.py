#!/usr/local/munki/munki-python

import os
import plistlib
import sys

sys.path.append("/usr/local/munki")

from munkilib import dmgutils
from munkilib import pkgutils

if len(sys.argv) != 2:
    print('Need exactly one parameter: path to a munki repo!', file=sys.stderr)
    sys.exit(-1)

repo_path = sys.argv[1]

all_catalog = os.path.join(repo_path, "catalogs/all")

with open(all_catalog, mode="rb") as FILE:
    all_items = plistlib.load(FILE)

dmg_items = [{"name": item["name"],
              "version": item["version"],
              "location": item["installer_item_location"],
              "package_path": item.get("package_path", "")} 
             for item in all_items
             if item.get("installer_item_location", "").endswith(".dmg") and  
             item.get("installer_type") is None]

items_with_bundle_style_pkgs = []
for item in dmg_items:
    full_path = os.path.join(repo_path, "pkgs", item["location"])
    print("Checking %s..." % full_path)
    mountpoints = dmgutils.mountdmg(full_path)
    if mountpoints:
        pkg_path = item["package_path"]
        if pkg_path:
            itempath = os.path.join(mountpoints[0], pkg_path)
            if os.path.isdir(itempath):
                print("***** %s--%s has a bundle-style pkg"
                      % (item["name"], item["version"]))
                items_with_bundle_style_pkgs.append(item)
        else:
            for file_item in os.listdir(mountpoints[0]):
                if pkgutils.hasValidInstallerItemExt(file_item):
                    itempath = os.path.join(mountpoints[0], file_item)
                    if os.path.isdir(itempath):
                        print("***** %s--%s has a bundle-style pkg" 
                              % (item["name"], item["version"]))
                        items_with_bundle_style_pkgs.append(item)
                        break
        dmgutils.unmountdmg(mountpoints[0])
    else:
        print("No filesystems mounted from %s" % full_path)
        continue

print("Found %s items with bundle-style pkgs."
      % len(items_with_bundle_style_pkgs))
for item in sorted(items_with_bundle_style_pkgs, key=lambda d: d["name"]):
    print("%s--%s"% (item["name"], item["version"]))
    print("    %s" % item["location"])

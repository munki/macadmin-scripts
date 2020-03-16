### installinstallmacos.py

A script to download the components for a macOS installer from Apple's softwareupdate servers and then install those components as a working "Install macOS High Sierra.app" onto a disk image.

The install logic within Apple's packages will be evaluated by Apple's installer, so you must run this on hardware compatible with the version of macOS for which you are attempting to obtain an installer. In other words, this script will fail when run on hardware that does not support High Sierra, and should High Sierra be "forked" as it was when the iMac Pro was first shipped, you may only be able to successfully install a hardware-specific version of the installer on the hardware supported by that specific build.

You'll need roughly twice the ultimate storage space; IOW if the High Sierra installer is 6GB you'll need at least 12GB free. If you use the --compress option you may need up to three times the space.

This tool must be run as root or with `sudo`.


#### Options

`--catalogurl` Software Update catalog URL used by the tool. Defaults to the default softwareupdate catalog for the current OS if you run this tool under macOS 10.13-10.15.x.

`--seedprogram SEEDPROGRAMNAME` Attempt to find and use the Seed catalog for the current OS. Use `installinstallmacos.py --help` to see the valid SeedProgram names for the current OS.

`--workdir` Path to working directory on a volume with over 10G of available space. Defaults to current working directory.

`--compress` Output a read-only compressed disk image with the Install macOS app at the root. This is slower and requires much more working disk space than the default, but the end product is more useful with tools like Munki and Imagr.

`--ignore-cache` Ignore any previously cached files. All needed files will be re-downloaded from the softwareupdate server.


#### Example operation

```
% sudo ./installinstallmacos.py 
Downloading https://swscan.apple.com/content/catalogs/others/index-10.13seed-10.13-10.12-10.11-10.10-10.9-mountainlion-lion-snowleopard-leopard.merged-1.sucatalog...
Downloading http://swcdn.apple.com/content/downloads/16/14/091-62779/frfttxz116hdm02ajg89z3cubtiv64r39s/InstallAssistantAuto.smd...
Downloading https://swdist.apple.com/content/downloads/16/14/091-62779/frfttxz116hdm02ajg89z3cubtiv64r39s/091-62779.English.dist...
Downloading http://swcdn.apple.com/content/downloads/10/62/091-76233/v27a64q1zvxd2lbw4gbej9c2s5gxk6zb1l/InstallAssistantAuto.smd...
Downloading https://swdist.apple.com/content/downloads/10/62/091-76233/v27a64q1zvxd2lbw4gbej9c2s5gxk6zb1l/091-76233.English.dist...
Downloading http://swcdn.apple.com/content/downloads/45/61/091-71284/77pnhgsj5oza9h28y7vjjtby8s1binimnj/InstallAssistantAuto.smd...
Downloading https://swdist.apple.com/content/downloads/45/61/091-71284/77pnhgsj5oza9h28y7vjjtby8s1binimnj/091-71284.English.dist...
 #    ProductID    Version    Build  Title
 1    091-76233    10.13.4   17E199  Install macOS High Sierra
 2    091-62779    10.13.3  17D2047  Install macOS High Sierra
 3    091-71284    10.13.4  17E160g  Install macOS High Sierra Beta

Choose a product to download (1-3): 1
Downloading http://swcdn.apple.com/content/downloads/10/62/091-76233/v27a64q1zvxd2lbw4gbej9c2s5gxk6zb1l/BaseSystem.chunklist...
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  1984  100  1984    0     0  65636      0 --:--:-- --:--:-- --:--:-- 66133
Downloading http://swcdn.apple.com/content/downloads/10/62/091-76233/v27a64q1zvxd2lbw4gbej9c2s5gxk6zb1l/InstallESDDmg.pkg...
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 4501M  100 4501M    0     0  30.9M      0  0:02:25  0:02:25 --:--:-- 30.7M
Downloading https://swdist.apple.com/content/downloads/10/62/091-76233/v27a64q1zvxd2lbw4gbej9c2s5gxk6zb1l/InstallESDDmg.pkm...
Downloading http://swcdn.apple.com/content/downloads/10/62/091-76233/v27a64q1zvxd2lbw4gbej9c2s5gxk6zb1l/InstallInfo.plist...
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  1584  100  1584    0     0  78025      0 --:--:-- --:--:-- --:--:-- 79200
Downloading http://swcdn.apple.com/content/downloads/10/62/091-76233/v27a64q1zvxd2lbw4gbej9c2s5gxk6zb1l/RecoveryHDMetaDmg.pkg...
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  464M  100  464M    0     0  25.3M      0  0:00:18  0:00:18 --:--:-- 31.2M
Downloading https://swdist.apple.com/content/downloads/10/62/091-76233/v27a64q1zvxd2lbw4gbej9c2s5gxk6zb1l/RecoveryHDMetaDmg.pkm...
Downloading http://swcdn.apple.com/content/downloads/10/62/091-76233/v27a64q1zvxd2lbw4gbej9c2s5gxk6zb1l/AppleDiagnostics.chunklist...
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   328  100   328    0     0  16419      0 --:--:-- --:--:-- --:--:-- 17263
Downloading http://swcdn.apple.com/content/downloads/10/62/091-76233/v27a64q1zvxd2lbw4gbej9c2s5gxk6zb1l/BaseSystem.dmg...
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  462M  100  462M    0     0  34.7M      0  0:00:13  0:00:13 --:--:-- 38.7M
Downloading http://swcdn.apple.com/content/downloads/10/62/091-76233/v27a64q1zvxd2lbw4gbej9c2s5gxk6zb1l/AppleDiagnostics.dmg...
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 2586k  100 2586k    0     0  10.6M      0 --:--:-- --:--:-- --:--:-- 10.6M
Downloading http://swcdn.apple.com/content/downloads/10/62/091-76233/v27a64q1zvxd2lbw4gbej9c2s5gxk6zb1l/InstallAssistantAuto.pkg...
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 11.2M  100 11.2M    0     0  19.5M      0 --:--:-- --:--:-- --:--:-- 19.5M
Downloading https://swdist.apple.com/content/downloads/10/62/091-76233/v27a64q1zvxd2lbw4gbej9c2s5gxk6zb1l/InstallAssistantAuto.pkm...
Downloading http://swcdn.apple.com/content/downloads/10/62/091-76233/v27a64q1zvxd2lbw4gbej9c2s5gxk6zb1l/InstallESDDmg.chunklist...
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 16528  100 16528    0     0   493k      0 --:--:-- --:--:-- --:--:--  504k
Downloading http://swcdn.apple.com/content/downloads/10/62/091-76233/v27a64q1zvxd2lbw4gbej9c2s5gxk6zb1l/OSInstall.mpkg...
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  658k  100  658k    0     0  4481k      0 --:--:-- --:--:-- --:--:-- 4509k
Making empty sparseimage...
installer: Package name is Install macOS High Sierra
installer: Installing at base path /private/tmp/dmg.7Znuzg
installer: The install was successful.
Product downloaded and installed to /Users/Shared/munki-git/macadmin-scripts/Install_macOS_10.13.4-17E199.sparseimage
```
# Raspberry pi experiment collection

TODO - describe the repo a little

## System setup

The [docs](https://www.raspberrypi.com/documentation/computers/getting-started.html) are a great place to start and look for up-to-date reference details.  The following is loosely following this for the raspberry-pi 5 with nvme board on debian 13 trixie.pP

Non-pi steps on windows / mac:
1. Flash the base OS to an sd-card with the [official imager](https://www.raspberrypi.com/software/), configuring only the wifi network and username as other settings don't seem to propogate correctly.

Pi steps:
1. Connect ssd tophat, insert sd-card & boot up
2. Get OS onto nvme
   1. Either clone the sd-card with `dd` or the built-in sd-card copier util.
   2. Or flash a new OS with the rpi imager running on the pi itself.
3. Set boot-order to prefer nvme - `sudo raspi-config` > advanced options > boot order > select boot from nvme
4. Shutdown `poweroff` and remove sd-card.  We should now boot off the nvme ssd on the next start
5. Now is a good time to copy over the dotfiles from this repo into their appropriate locations in the PI os (can also be done at any point later)
6. Enable ssh `sudo systemctl enable ssh` - we will later configure it to block pw auth
7. Update system `sudo apt update && sudo apt upgrade`
8. Install dev packages `sudo apt install vim htop tmux code build-essential cmake ninja-build`
9. Configure a static ip which we need this to reliably connect to ssh.
   1. Get network details so we know what to configure
      1. `ip r` - tells us default gateway (router ip), current local ip and our netmask.
   2.   We can either use `sudo nmtui` or get to the same thing in the gui by clicking on the network widget on the taskbar
   3. Go edit connection > ipv4 configuration
      1. Set connection type to manual
      2. If you have a netmask option, figure it out from the cidr suffix on the current ip (`/24` would be `255.255.255.0`)
      3. Set the default gateway to the router ip
      4. For ip itself set it to something near the end of the valid range.
         1. e.g. with a gateway of `192.168.1.0`, netmask of `/24`, we should combine the first 3 bytes of the router ip with a value close to 255 such as `192.168.1.249`.
      5. Save and exit
10. If you can be sure the pi and your device will be connected to the same network endpoint, e.g. both on ethernet or the same access point if on wifi, setting a hostname makes connections easier later.  Get the current name with `cat /etc/hostname` or set a new one via `sudo echo '<new_hostname>' > /etc/hostname`
   1.  In any downstream steps, all references to the pi's IP can be replaced with `<new_hostname>.local` and it should just work.
11. Reboot
12. Move on to securing ssh (optional for prototyping but recommended otherwise)

From an external pc with ssh configured:
1. Copy over ssh keys `ssh-copy-id <username>@<py_local_ip>
2. Add a ssh config on the client pc to ~/.ssh/config:
```
Host pi
    Hostname <py_local_ip>
    Port 22
    User <username>
    IdentityFile /home/<user>/.ssh/<your_ssh_private_key>
    IdentitiesOnly yes
```
3. Check the connection works `ssh pi`, accepting fingerprint if required then close the session `CTRL + D`

Back on the pi:
1. Open the sshd config `sudo vim /etc/ssh/sshd_config`
2. Block password auth by uncommenting and / or setting the following values from the defaults:
```
PubkeyAuthentication yes

PasswordAuthentication no
PermitEmptyPasswords no
```
3. Save the config and check any sub-configs do not have conflicting settings, e.g. check all files under `/etc/ssh/sshd_confg.d/*.conf`
   1. If there are then ensure those are set to the same as above

Extra steps:
- Make new or copy existing ssh keys onto the pi to let it access whatever machines it needs and authenticate to git repos

### Camera setup:

Refer to the [camera section](https://www.raspberrypi.com/documentation/computers/camera_software.html) of the docs for up-to-date steps.
1. Install camera module via ribbon cable, making sure the pi is not powered on
2. Boot up, install camera utils `sudo apt install rpicam-apps`
3. Check the camera is detected `rpicam-hello --list-cameras`
4. If the module is present, run a test capture `rpicam-hello --framerate 60`

#### Camera quirks

1. The pi 5 has no hardware accleration for video encoding, everything runs on cpu even with running with the libav codec or `--low-latency`, so overclocking & thermal management might be required for optimal performance.
2. The camera device `/dev/video0` cannot be accessed directly, e.g. for setting up a direct [ffmpeg stream](https://forums.raspberrypi.com/viewtopic.php?t=384403)

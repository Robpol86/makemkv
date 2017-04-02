# Headless DVD/BD Backups with MakeMKV

> NOTE: This repo is a work in progress.

Automatically backup your DVD and Bluray discs to local storage. When this Docker image is used together with
[udev rules](http://www.reactivated.net/writing_udev_rules.html) backups are as easy as inserting discs and then sitting
back until the drive ejects the disc. Rinse and repeat.

## Variables and Volumes

Below are the available environment variables you may use to configure this Docker image:

* **MKV_GID** The group ID of the `mkv` user inside the container.
* **MKV_UID** The user ID of the `mkv` user inside the container.
* **NO_EJECT** Disables ejecting the disc if set to "true".

And below are the available volumes used by the Docker image:

* **/output** Ripped MKV files are written to this directory inside the container.

## Run Manually

Before setting up the automated run it's a good idea to try running this manually to see the output it produces in case
there are any compatibility or other issues. First make sure you've got your optical drive plugged in (if it's external)
and that you can see `/dev/cdrom` on your system:

```
$ ls -lah /dev/cdrom
lrwxrwxrwx. 1 root root 3 Mar 31 17:12 /dev/cdrom -> sr0
```

Now go ahead and run the image:

```bash
mkdir ~/videos
sudo docker run -it \
    --device=/dev/cdrom \
    -e MKV_GID=$(id -g) \
    -e MKV_UID=$(id -u) \
    -v ~/videos:/output \
    robpol86/makemkv
```

You should see something like this:

```
Unable to find image 'robpol86/makemkv:latest' locally
latest: Pulling from robpol86/makemkv
bc5187a39b05: Already exists
3d9a191cc067: Pull complete
fe1343ee5111: Pull complete
f9e562c653cd: Pull complete
50304eac31e3: Pull complete
Digest: sha256:88e4bf005b0b0dfc3d7f3da85713aec9542f8ed213790864b6a7cdc500f7fbc1
Status: Downloaded newer image for robpol86/makemkv:latest
Ripping...
MakeMKV v1.10.5 linux(x64-release) started
Current operation: Scanning CD-ROM devices
Current action: Scanning CD-ROM devices
Current progress - 0%  , Total progress - 0%
...
Current progress - 92%  , Total progress - 0%
Current action: Saving to MKV file
Current progress - 0%  , Total progress - 0%
...
Current progress - 100%  , Total progress - 100%
8 titles saved
Copy complete. 8 titles saved.
Ejecting...
Done
```
## Automated Run

TODO

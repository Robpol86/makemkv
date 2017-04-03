# Headless DVD/BD Backups with MakeMKV

> NOTE: This repo is a work in progress.

Automatically backup your DVD and Bluray discs to local storage. When this Docker image is used together with
[udev rules](http://www.reactivated.net/writing_udev_rules.html) backups are as easy as inserting discs and then sitting
back until the drive ejects the disc. Rinse and repeat.

Note this Docker image only decrypts and rips to MKV files. It does not transcode/convert files into smaller sizes or
other formats. Ripping Blurays may take up around **40 GB** or so in my experience.

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
mkdir ~/MakeMKV
sudo docker run -it \
    --device=/dev/cdrom \
    -e MKV_GID=$(id -g) \
    -e MKV_UID=$(id -u) \
    -v ~/MakeMKV:/output \
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
Digest: sha256:88e4bf005b0b0dfc3d7f3da85713aec9542f8ed213790864b6a7cdc
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

Once you've verified this Docker image works fine on your system it's time to automate it. Lets start off with a simple
udev rule that runs the image and then cleans up by deleting the container after it's done ripping (leaving the ripped
files intact since they're in a volume). Create the following rules file and replace the user `you` with your non-root
username.

```
# Save as: /etc/udev/rules.d/85-makemkv.rules
SUBSYSTEM=="block", KERNEL=="sr[0-9]*", ACTION=="change", ENV{ID_FS_TYPE}=="udf", \
RUN+="/usr/bin/docker run -d --rm --device=%E{DEVNAME} -e MKV_GID=1000 -e MKV_UID=1000 -v /home/you/MakeMKV:/output robpol86/makemkv"
```

After saving the file you don't need to reload anything or reboot. It should Just Work. Insert a disc and look for the
container in `sudo docker ps`.

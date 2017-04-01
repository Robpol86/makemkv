# Headless DVD/BD Backups with MakeMKV

> NOTE: This repo is a work in progress.

Automated headless DVD/Bluray backups with MakeMKV from Docker.

## Run Manually

Before setting up the automated run it's a good idea to try running it manually to see the output `makemkvcon` produces
in case there are any compatibility or other issues.

Before pulling/running this Docker image make sure you've got your optical drive plugged in (if it's external) and that
you can see `/dev/cdrom` on your system:

```
$ ls -lah /dev/cdrom
lrwxrwxrwx. 1 root root 3 Mar 31 17:12 /dev/cdrom -> sr0
```

Now go ahead and run the image (note: if you exclude `-it` you'll need to run `sudo docker stop <container>` since
`ctrl+c` won't work):

```bash
sudo docker run -it --device=/dev/cdrom -v ~/videos:/output robpol86/makemkv
```

You should see something like this:

```
TODO
```
## Automated Run

TODO

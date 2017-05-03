FROM robpol86/rpmdevtools-fedora:25
MAINTAINER Robpol86 <robpol86@gmail.com>

VOLUME /output
WORKDIR /output

CMD gcc -o wrappers.so wrappers.c -fPIC -shared -lprocps

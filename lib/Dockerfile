FROM robpol86/makemkv
MAINTAINER Robpol86 <robpol86@gmail.com>

RUN dnf install -y gcc

VOLUME /output
WORKDIR /output

CMD gcc -o wrappers.so wrappers.c -fPIC -shared -lprocps

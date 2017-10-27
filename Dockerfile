FROM fedora:25
MAINTAINER Robpol86 <robpol86@gmail.com>

RUN dnf update -qy && \
    dnf install -qy dnf-plugins-core sudo && \
    dnf config-manager --add-repo=http://negativo17.org/repos/fedora-multimedia.repo && \
    dnf install -qy makemkv && \
    dnf install -y awscli && \
    dnf clean all && \
    sudo useradd -s /sbin/nologin -G cdrom mkv && \
    sudo -u mkv mkdir /home/mkv/.MakeMKV

VOLUME /output
WORKDIR /output
COPY bin/env.sh /
COPY bin/rip.sh /
COPY etc/settings.conf /home/mkv/.MakeMKV/
COPY lib/wrappers.so /
COPY hook-post-title.sh /
COPY hook-end.sh /
COPY hook-post-on-err.sh /

CMD ["/rip.sh | tee /var/log/makemkv.log"]

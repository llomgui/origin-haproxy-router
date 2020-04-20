FROM centos:7 AS RPM

ARG HAPROXY_VERSION

RUN yum groupinstall -y 'Development Tools'
RUN mkdir -p /opt && yum install -y pcre-devel pcre-devel make gcc openssl-devel rpm-build systemd-devel sed wget
WORKDIR /builder

ADD haproxy .

RUN rm -f ./SOURCES/haproxy-${HAPROXY_VERSION}.tar.gz \
    && rm -rf ./rpmbuild \
    && mkdir -p ./rpmbuild/SPECS/ ./rpmbuild/SOURCES/ ./rpmbuild/RPMS/ ./rpmbuild/SRPMS/

RUN wget http://www.haproxy.org/download/1.8/src/haproxy-${HAPROXY_VERSION}.tar.gz -O ./SOURCES/haproxy-${HAPROXY_VERSION}.tar.gz

RUN cp -r ./SPECS/* ./rpmbuild/SPECS/ || true \
    && cp -r ./SOURCES/* ./rpmbuild/SOURCES/ || true

RUN rpmbuild -ba SPECS/haproxy.spec \
    --define "_topdir %(pwd)/rpmbuild" \
    --define "_builddir %{_topdir}/BUILD" \
    --define "_buildroot %{_topdir}/BUILDROOT" \
    --define "_rpmdir %{_topdir}/RPMS" \
    --define "_srcrpmdir %{_topdir}/SRPMS"

FROM openshift/origin-haproxy-router:v3.11.0

COPY --from=RPM /builder/rpmbuild/RPMS/x86_64/haproxy18*.rpm /tmp/

USER 0

RUN yum update -y \
    && yum localinstall -y /tmp/haproxy18*.rpm && rm -f tmp/haproxy18*.rpm \
    && yum clean all \
    && setcap 'cap_net_bind_service=ep' /usr/sbin/haproxy

USER 1001
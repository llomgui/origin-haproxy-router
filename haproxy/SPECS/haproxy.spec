%define haproxy_user    haproxy
%define haproxy_group   %{haproxy_user}
%define haproxy_home    %{_localstatedir}/lib/haproxy
%define haproxy_confdir %{_sysconfdir}/haproxy
%define haproxy_datadir %{_datadir}/haproxy

%global _hardened_build 1

%define real_name haproxy18

Name:           haproxy
Version:        1.8.25
Release:        1%{?dist}
Summary:        Do not ship, install or use this, use %{real_name} subpackage instead

License:        GPLv2+

URL:            http://www.haproxy.org/
Source0:        http://www.haproxy.org/download/1.8/src/haproxy-%{version}.tar.gz
Source1:        %{name}.service
Source2:        %{name}.cfg
Source3:        %{name}.logrotate
Source4:        %{name}.sysconfig
Source5:        halog.1

#BuildRequires:  lua-devel
BuildRequires:  pcre-devel
BuildRequires:  zlib-devel
BuildRequires:  openssl-devel
BuildRequires:  systemd-units
BuildRequires:  systemd-devel

%package -n %{real_name}
Summary:            TCP/HTTP proxy and load balancer for high availability environments
Group:              System Environment/Daemons
Requires(pre):      shadow-utils
Requires(post):     systemd
Requires(preun):    systemd
Requires(postun):   systemd

Conflicts:          haproxy

%description
Do not ship, install or use this, use %{real_name} subpackage instead

%description -n %{real_name}
HAProxy is a TCP/HTTP reverse proxy which is particularly suited for high
availability environments. Indeed, it can:
 - route HTTP requests depending on statically assigned cookies
 - spread load among several servers while assuring server persistence
   through the use of HTTP cookies
 - switch to backup servers in the event a main server fails
 - accept connections to special ports dedicated to service monitoring
 - stop accepting connections without breaking existing ones
 - add, modify, and delete HTTP headers in both directions
 - block requests matching particular patterns
 - report detailed status to authenticated users from a URI
   intercepted by the application

%prep
%setup -q

%build
regparm_opts=
%ifarch %ix86 x86_64
regparm_opts="USE_REGPARM=1"
%endif

%{__make} %{?_smp_mflags} CPU="generic" TARGET="linux2628" USE_OPENSSL=1 USE_PCRE=1 USE_ZLIB=1 ${regparm_opts} ADDINC="%{optflags}" USE_LINUX_TPROXY=1 ADDLIB="%{__global_ldflags}" DEFINE=-DTCP_USER_TIMEOUT=18 USE_SYSTEMD=1
#USE_LUA=1

pushd contrib/halog
%{__make} halog OPTIMIZE="%{optflags}"
popd

pushd contrib/iprange
%{__make} iprange OPTIMIZE="%{optflags}"
popd

%install
%{__make} install-bin DESTDIR=%{buildroot} PREFIX=%{_prefix} TARGET="linux2628"
%{__make} install-man DESTDIR=%{buildroot} PREFIX=%{_prefix}

%{__install} -p -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/%{name}.service
%{__install} -p -D -m 0644 %{SOURCE2} %{buildroot}%{haproxy_confdir}/%{name}.cfg
%{__install} -p -D -m 0644 %{SOURCE3} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
%{__install} -p -D -m 0644 %{SOURCE4} %{buildroot}%{_sysconfdir}/sysconfig/%{name}
%{__install} -p -D -m 0644 %{SOURCE5} %{buildroot}%{_mandir}/man1/halog.1
%{__install} -d -m 0755 %{buildroot}%{haproxy_home}
%{__install} -d -m 0755 %{buildroot}%{haproxy_datadir}
%{__install} -d -m 0755 %{buildroot}%{_bindir}
%{__install} -p -m 0755 ./contrib/halog/halog %{buildroot}%{_bindir}/halog
%{__install} -p -m 0755 ./contrib/iprange/iprange %{buildroot}%{_bindir}/iprange
%{__install} -p -m 0644 ./examples/errorfiles/* %{buildroot}%{haproxy_datadir}

for httpfile in $(find ./examples/errorfiles/ -type f)
do
    %{__install} -p -m 0644 $httpfile %{buildroot}%{haproxy_datadir}
done

%{__rm} -rf ./examples/errorfiles/

find ./examples/* -type f ! -name "*.cfg" -exec %{__rm} -f "{}" \;

for textfile in $(find ./ -type f -name "*.txt" -o -name README)
do
    %{__mv} $textfile $textfile.old
    iconv --from-code ISO8859-1 --to-code UTF-8 --output $textfile $textfile.old
    %{__rm} -f $textfile.old
done

%pre -n %{real_name}
getent group %{haproxy_group} >/dev/null || groupadd -f -g 188 -r %{haproxy_group}
if ! getent passwd %{haproxy_user} >/dev/null ; then
    if ! getent passwd 188 >/dev/null ; then
        useradd -r -u 188 -g %{haproxy_group} -d %{haproxy_home} -s /sbin/nologin -c "haproxy" %{haproxy_user}
    else
        useradd -r -g %{haproxy_group} -d %{haproxy_home} -s /sbin/nologin -c "haproxy" %{haproxy_user}
    fi
fi

%post -n %{real_name}
%systemd_post %{name}.service

%preun -n %{real_name}
%systemd_preun %{name}.service

%postun -n %{real_name}
%systemd_postun_with_restart %{name}.service

%files -n %{real_name}
%defattr(-,root,root,-)
%doc doc/* examples/
%doc CHANGELOG LICENSE README ROADMAP VERSION
%dir %{haproxy_confdir}
%dir %{haproxy_datadir}
%{haproxy_datadir}/*
%config(noreplace) %{haproxy_confdir}/%{name}.cfg
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%{_unitdir}/%{name}.service
%{_sbindir}/%{name}
#systemd-wrapper no longer needed since 1.8
#% {_sbindir}/% {name}-systemd-wrapper
%{_bindir}/halog
%{_bindir}/iprange
%{_mandir}/man1/*
%attr(-,%{haproxy_user},%{haproxy_group}) %dir %{haproxy_home}

%changelog
* Wed Apr 01 2020 Dan Mace <dmace@redhat.com> - 1.8.23-3
- Resolve CVE-2020-11100 (https://bugzilla.redhat.com/show_bug.cgi?id=1819111)

* Tue Mar 24 2020 Andrew McDermott <amcdermo@redhat.com> - 1.8.23-2
- Fixes sources line

* Wed Feb 12 2020 Andrew McDermott <amcdermo@redhat.com> - 1.8.23-1
- Update to 1.8.23 (#1781027)
- Resolve CVE-2019-19330 (#1781028 #1781029)

* Thu Jan 17 2019 Frantisek Kluknavsky <fkluknav@redhat.com> - 1.8.17-3
- rebase

* Tue Sep 25 2018 Frantisek Kluknavsky <fkluknav@redhat.com> - 1.8.14-2
- rebase

* Fri Apr 20 2018 Frantisek Kluknavsky <fkluknav@redhat.com> - 1.8.8-1
- rebase
- patches already upstream, removed
- RHBZ#1569297

* Wed Jan 10 2018 Scott Dodson <sdodson@redhat.com> - 1.8.1-5
- Run pre scriptlet on haproxy18
* Wed Jan 03 2018 Frantisek Kluknavsky <fkluknav@redhat.com> - 1.8.1-4
- conflicts: haproxy

* Wed Jan 03 2018 Frantisek Kluknavsky <fkluknav@redhat.com> - 1.8.1-3
- rebuilt for rhaos-3.8-rhel-7

* Wed Dec 20 2017 Frantisek Kluknavsky <fkluknav@redhat.com> - 1.8.1-2
- rebase

* Thu Oct 26 2017 Frantisek Kluknavsky <fkluknav@redhat.com> - 1.7.9-1
- rebase

* Mon May 01 2017 Ryan O'Hara <rohara@redhat.com> - 1.5.18-6
- Use KillMode=mixed in systemd service file (#1444709)

* Thu Mar 16 2017 Ryan O'Hara <rohara@redhat.com> - 1.5.18-5
- Use soft-static allocation for haproxy UID/GID (#1386130)

* Wed Nov 16 2016 Ryan O'Hara <rohara@redhat.com> - 1.5.18-4
- Return correct exit codes from systemd-wrapper (#1391990)

* Tue Jun 21 2016 Ryan O'Hara <rohara@redhat.com> - 1.5.18-3
- Fix TCP user timeout patch for 1.5.18 release

* Thu Jun 16 2016 Ryan O'Hara <rohara@redhat.com> - 1.5.18-2
- Add TARGET to install-bin for haproxy-systemd-wrapper

* Wed Jun 15 2016 Ryan O'Hara <rohara@redhat.com> - 1.5.18-1
- Update to stable release 1.5.18 (#1344012)

* Tue Aug 25 2015 Ryan O'Hara <rohara@redhat.com> - 1.5.14-3
- Add EnvironmentFile to systemd service (#1191675)

* Mon Jul 06 2015 Ryan O'Hara <rohara@redhat.com> - 1.5.14-1
- Update to stable release 1.5.14 (CVE-2015-3281, #1212193)

* Wed Jun 24 2015 Ryan O'Hara <rohara@redhat.com> - 1.5.12-2
- Rebase TCP uset timeout patch for 1.5.12 release (#1212193)

* Tue Jun 23 2015 Ryan O'Hara <rohara@redhat.com> - 1.5.12-1
- Update to stable release 1.5.12 (#1212193)

* Thu May 21 2015 Ryan O'Hara <rohara@redhat.com> - 1.5.4-5
- Define TCP_USER_TIMEOUT at build time (#1190776)

* Wed Mar 04 2015 Ryan O'Hara <rohara@redhat.com> - 1.5.4-4
- Read sysconfig file for extra options (#1191675)

* Wed Mar 04 2015 Ryan O'Hara <rohara@redhat.com> - 1.5.4-3
- Add tcp-ut bind option to set TCP_USER_TIMEOUT (#1190776)

* Tue Nov 18 2014 Ryan O'Hara <rohara@redhat.com> - 1.5.4-2
- Fix date in changelog

* Tue Sep 02 2014 Ryan O'Hara <rohara@redhat.com> - 1.5.4-1
- Update to stable release 1.5.4 (#1111714)

* Fri Jul 25 2014 Ryan O'Hara <rohara@redhat.com> - 1.5.3-1
- Update to stable release 1.5.3 (#1111714)

* Tue Jul 15 2014 Ryan O'Hara <rohara@redhat.com> - 1.5.2-1
- Update to stable release 1.5.2 (#1111714)

* Tue Jul 08 2014 Ryan O'Hara <rohara@redhat.com> - 1.5.1-6
- Cleanup spec file (#1068642)

* Tue Jul 08 2014 Ryan O'Hara <rohara@redhat.com> - 1.5.1-5
- Minor changes to summary and description (#1067146)

* Tue Jul 08 2014 Ryan O'Hara <rohara@redhat.com> - 1.5.1-4
- Include iprange tool (#1078487)

* Tue Jul 08 2014 Ryan O'Hara <rohara@redhat.com> - 1.5.1-3
- Include man page for halog (#1078461)

* Tue Jul 08 2014 Ryan O'Hara <rohara@redhat.com> - 1.5.1-2
- Build with openssl and zlib (#1112184)

* Tue Jul 08 2014 Ryan O'Hara <rohara@redhat.com> - 1.5.1-1
- Update to stable release 1.5.1 (#1111714)

* Fri Feb 28 2014 Ryan O'Hara <rohara@redhat.com> - 1.5-0.3.dev22
- Use haproxy-systemd-wrapper in service file (#1067060)

* Wed Feb 12 2014 Ryan O'Hara <rohara@redhat.com> - 1.5-0.2.dev22
- Specify assigned UID in useradd

* Mon Feb 10 2014 Ryan O'Hara <rohara@redhat.com> - 1.5-0.1.dev22
- Update to development release 1.5-dev22 (#1043658)

* Fri Jan 24 2014 Daniel Mach <dmach@redhat.com> - 1.4.24-3
- Mass rebuild 2014-01-24

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 1.4.24-2
- Mass rebuild 2013-12-27

* Mon Jun 17 2013 Ryan O'Hara <rohara@redhat.com> - 1.4.24-1
- Update to 1.4.24 (CVE-2013-2174, #975160)

* Tue Apr 30 2013 Ryan O'Hara <rohara@redhat.com> - 1.4.23-3
- Build with PIE flags (#955182)

* Mon Apr 22 2013 Ryan O'Hara <rohara@redhat.com> - 1.4.23-2
- Build with PIE flags (#955182)

* Tue Apr 02 2013 Ryan O'Hara <rohara@redhat.com> - 1.4.23-1
- Update to 1.4.23 (CVE-2013-1912, #947697)
- Drop supplementary groups after setuid/setgid (#894626)

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4.22-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Fri Oct 12 2012 Robin Lee <cheeselee@fedoraproject.org> - 1.4.22-1
- Update to 1.4.22 (CVE-2012-2942, #824544)
- Use linux2628 build target
- No separate x86_64 build target for halog
- halog build honors rpmbuild optflags
- Specfile cleanup

* Mon Sep 17 2012 Václav Pavlín <vpavlin@redhat.com> - 1.4.20-3
- Scriptlets replaced with new systemd macros (#850143)

* Thu Jul 19 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4.20-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Apr 03 2012 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.4.20-1
- Update to 1.4.20

* Sun Feb 19 2012 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.4.19-4
- fix haproxy.services file

* Sun Feb 19 2012 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.4.19-3
- Update to use systemd fixing bug #770305

* Fri Feb 10 2012 Petr Pisar <ppisar@redhat.com> - 1.4.19-2
- Rebuild against PCRE 8.30

* Sun Jan 29 2012 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.4.19-1
- Update to 1.4.19

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4.18-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Thu Sep 22 2011 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.4.18-1
- Update to 1.4.18

* Tue Apr 26 2011 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.4.15-1
- Update to 1.4.15

* Sun Feb 27 2011 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.4.11-1
- update to 1.4.11

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Sun Dec 12 2010 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.4.9-1
- update to 1.4.9

* Sun Jun 20 2010 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.4.8-1
- update to 1.4.8

* Sun May 30 2010 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.4.6-1
- update to 1.4.6

* Thu Feb 18 2010 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.3.23-1
- update to 1.3.23

* Sat Oct 17 2009 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.3.22-1
- update to 1.3.22
- added logrotate configuration

* Mon Oct 12 2009 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.3.21-1
- update to 1.3.21

* Sun Oct 11 2009 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.3.20-1
- update to 1.3.20

* Sun Aug 02 2009 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.3.19-1
- update to 1.3.19

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.18-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Sun May 17 2009 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.3.18-1
- update to 1.3.18

* Sat Apr 11 2009 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.3.17-1
-  Update to 1.3.17

* Tue Feb 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.15.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Tue Dec 30 2008 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.3.15.7-1
- update to 1.3.15.7
- remove upstream patches, they are now part of source distribution

* Sat Nov 22 2008 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.3.15.6-2
- apply upstream patches

* Sat Nov 15 2008 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.3.15.6-1
- update to 1.3.15.6
- use new build targets from upstream
- add in recommended build options for x86 from upstream

* Sat Jun 28 2008 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.3.14.6-1
- update to 1.3.14.6
- remove gcc 4.3 patch, it has been applied upstream
- remove MIT license as that code has been removed from upstream

* Mon Apr 14 2008 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.3.14.4-1
- update to 1.3.14.4

* Sun Mar 16 2008 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.3.14.3-1
- update to 1.3.14.3

* Sat Mar 01 2008 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.3.14.2-4
- apply the gcc 4.3 patch to the build process

* Sat Mar 01 2008 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.3.14.2-3
- fix gcc 4.3 bug [#434144]
- update init script to properly reload configuration

* Tue Feb 19 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 1.3.14.2-2
- Autorebuild for GCC 4.3

* Sun Jan 20 2008 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.3.14.2-1
- update to 1.3.14.2
- update make flags that changed with this upstream release
- added man page installation

* Sun Dec 16 2007 Jeremy Hinegardner <jeremy at hinegardner dot org> - 1.3.14-1
- update to 1.3.14

* Mon Nov 05 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 1.3.12.4-1
- update to 1.3.12.4

* Thu Nov 01 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 1.3.12.3-1
- update to 1.3.12.3

* Fri Sep 21 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 1.3.12.2-3
- fix init script 'reload' task

* Thu Sep 20 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 1.3.12.2-2
- update License field

* Thu Sep 20 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 1.3.12.2-1
- update to 1.3.12.2
- remove the upstream patch

* Tue Sep 18 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 1.3.12.1-1
- switch to 1.3.12.1 branch
- add patch from upstream with O'Reilly licensing updates.
- convert ISO-8859-1 doc files to UTF-8

* Sat Mar 24 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 1.2.17-2
- addition of haproxy user
- add license information

* Fri Mar 23 2007 Jeremy Hinegardner <jeremy@hinegardner.org> - 1.2.17-1
- initial packaging

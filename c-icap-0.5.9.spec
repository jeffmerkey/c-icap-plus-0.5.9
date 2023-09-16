%define _build_id_links none
%define debug_package %{nil}

%define modn      c_icap
%global __brp_mangle_shebangs /usr/bin/true

Summary:          An implementation of an ICAP server
Name:             c-icap
Version:          0.5.9
Release:          1%{?dist}
License:          LGPL

Source0:          http://sourceforge.net/projects/c-icap/files/c-icap/0.5.x/%{name}-%{version}.tar.gz
Source1:          %{name}.service
Source2:          %{name}.sysconfig
Source3:          %{name}.logrotate
Source4:          %{name}.tmpfiles.conf

URL:              http://%{name}.sourceforge.net/

## Patches
Patch1:           c-icap-info-0.5.9-1.patch
Patch2:           c-icap-mpmt-0.5.9.patch
Patch3:           c-icap-perl.patch
Patch4:           c-icap-logs.patch
Patch5:           c-icap-md5.patch

Requires:         %{name}-libs = %{version}-%{release}
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd
BuildRequires:    systemd
BuildRequires:    gdbm-devel openldap-devel
BuildRequires:    zlib-devel perl-devel brotli-devel
BuildRequires:    libdb-devel
#BuildRequires:    db4-devel

%description
C-icap is an implementation of an ICAP server. It can be used with HTTP
proxies that support the ICAP protocol to implement content adaptation
and filtering services. Most of the commercial HTTP proxies must support
the ICAP protocol, the open source Squid 3.x proxy server supports it too.

%package          devel
Summary:          Development tools for %{name}
Group:            Development/Libraries
Requires:         %{name}-libs = %{version}-%{release}
Requires:         zlib-devel brotli-devel

%description      devel
The %{name}-devel package contains the static libraries and header files
for developing software using %{name}.
# RUN_AS="c-icap"

%package          ldap
Summary:          The LDAP module for %{name}
Group:            System Environment/Libraries
Requires:         %{name} = %{version}-%{release}

%description      ldap
The %{name}-ldap package contains the LDAP module for %{name}.


%package          libs
Summary:          Libraries used by %{name}
Group:            System Environment/Libraries

%description      libs
The %{name}-libs package contains all runtime libraries used by %{name} and
the utilities.


%package          perl
Summary:          The Perl handler for %{name}
Group:            System Environment/Libraries
Requires:         %{name} = %{version}-%{release}

%description      perl
The %{name}-perl package contains the Perl handler for %{name}.

%package          progs
Summary:          Related programs for %{name}
Group:            Applications/Internet
Requires:         %{name}-libs = %{version}-%{release}

%description      progs
The %{name}-progs package contains several commandline tools for %{name}.


%prep
%setup -q -n %{modn}-%{version}
%patch1 -p1 
%patch2 -p1 
%patch3 -p1 
%patch4 -p1 
%patch5 -p1 

%build
%configure \
	CFLAGS="${RPM_OPT_FLAGS} -fno-strict-aliasing" \
	--sysconfdir=%{_sysconfdir}/%{name}            \
	--enable-shared                                \
	--enable-static                                \
	--enable-lib-compat                            \
	--with-perl                                    \
	--with-zlib                                    \
	--with-bdb                                     \
	--with-ldap                                    \
        --enable-large-files				
#       --disable-poll
#	--enable-ipv6  # net.ipv6.bindv6only not supported

%{__make} %{?_smp_mflags}

%install
[ -n "%{buildroot}" -a "%{buildroot}" != "/" ] && %{__rm} -rf %{buildroot}
%{__mkdir_p} %{buildroot}%{_sysconfdir}/{logrotate.d,sysconfig}
%{__mkdir_p} %{buildroot}%{_sbindir}
%{__mkdir_p} %{buildroot}%{_datadir}/%{modn}/{contrib,templates}
%{__mkdir_p} %{buildroot}%{_localstatedir}/log/%{name}

%{__make} \
	DESTDIR=%{buildroot} \
	install

%{__mv}      -f      %{buildroot}%{_bindir}/%{name} %{buildroot}%{_sbindir}

%{__install} -m 0644 %{SOURCE2}   %{buildroot}%{_sysconfdir}/sysconfig/%{name}
%{__install} -m 0644 %{SOURCE3}   %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
%{__install} -D -p -m 0644 %{SOURCE4} %{buildroot}%{_tmpfilesdir}/%{name}.conf
%{__install} -D -m 644 %{SOURCE1} %{buildroot}%{_unitdir}/c-icap.service

%{__install} -m 0755 contrib/*.pl %{buildroot}%{_datadir}/%{modn}/contrib

%{__rm}      -f                   %{buildroot}%{_libdir}/lib*.so.{?,??}


%pre
if ! getent group  %{name} >/dev/null 2>&1; then
  /usr/sbin/groupadd -r %{name}
fi
if ! getent passwd %{name} >/dev/null 2>&1; then
  /usr/sbin/useradd  -r -g %{name}       \
	-d %{_localstatedir}/run/%{name} \
	-c "C-ICAP Service user" -M      \
	-s /sbin/nologin %{name}
fi
exit 0			# Always pass


%post
%systemd_post c-icap.service
systemctl enable c-icap >& /dev/null 

%post libs -p /sbin/ldconfig

%preun
%systemd_preun c-icap.service


%postun
%systemd_postun_with_restart c-icap.service

%postun libs -p /sbin/ldconfig

%files
%defattr(-,root,root)
%doc AUTHORS COPYING INSTALL README TODO
%attr(750,root,%{name}) %dir %{_sysconfdir}/%{name}
%attr(640,root,%{name}) %config(noreplace) %{_sysconfdir}/%{name}/*.conf
%attr(640,root,%{name}) %config(noreplace) %{_sysconfdir}/%{name}/*.magic
%attr(640,root,%{name}) %{_sysconfdir}/%{name}/*.default
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%{_unitdir}/c-icap.service 
%dir %{_libdir}/%{modn}
%{_libdir}/%{modn}/bdb_tables.so
%{_libdir}/%{modn}/dnsbl_tables.so
%{_libdir}/%{modn}/srv_echo.so
%{_libdir}/%{modn}/sys_logger.so
%{_libdir}/%{modn}/shared_cache.so
%{_sbindir}/%{name}
%{_datadir}/%{modn}
%{_mandir}/man8/%{name}.8*
%attr(750,%{name},%{name}) %dir %{_localstatedir}/log/%{name}
%attr(750,%{name},%{name}) %dir %{_localstatedir}/run/%{name}
%{_tmpfilesdir}/c-icap.conf

%files devel
%defattr(-,root,root)
%{_bindir}/%{name}-*config
%{_includedir}/%{modn}
%{_libdir}/libicapapi.*a
%{_libdir}/libicapapi.so
%{_libdir}/%{modn}/bdb_tables.*a
%{_libdir}/%{modn}/dnsbl_tables.*a
%{_libdir}/%{modn}/ldap_module.*a
%{_libdir}/%{modn}/perl_handler.*a
%{_libdir}/%{modn}/srv_echo.*a
%{_libdir}/%{modn}/sys_logger.*a
%{_libdir}/%{modn}/srv_ex206.*a
%{_libdir}/%{modn}/shared_cache.*a
%{_mandir}/man8/%{name}-*config.8*

%files ldap
%defattr(-,root,root)
%{_libdir}/%{modn}/ldap_module.so

%files libs
%defattr(-,root,root)
%doc COPYING
%{_libdir}/libicapapi.so.*

%{_libdir}/%{modn}/srv_ex206.so

%files perl
%defattr(-,root,root)
%{_libdir}/%{modn}/perl_handler.so

%files progs
%defattr(-,root,root)
%{_bindir}/%{name}-client
%{_bindir}/%{name}-mkbdb
%{_bindir}/%{name}-stretch
%{_mandir}/man8/%{name}-client.8*
%{_mandir}/man8/%{name}-mkbdb.8*
%{_mandir}/man8/%{name}-stretch.8*


%changelog

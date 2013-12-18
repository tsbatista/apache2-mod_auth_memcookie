Name:           mod_auth_memcookie
Version:        1.0.4
Release:        2%{?dist}
Summary:        Apache module for SSO authentication using information stored on a memcached server
Group:          System Environment/Daemons
License:        Apache 2.0
URL:            https://github.com/tsbatista/apache2-mod_auth_memcookie
Source:         https://github.com/tsbatista/apache2-mod_auth_memcookie/tsbatista/apache2-%{name}/archive/v%{version}.zip
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  httpd-devel libmemcache-devel
#selinux buildtime dependencies
BuildRequires: checkpolicy, selinux-policy-devel

####Requires:       httpd-mmn = %#(cat %{_includedir}/httpd/.mmn || echo missing-httpd-devel)
Requires: httpd libmemcache

%{!?_selinux_policy_version: %global _selinux_policy_version %(sed -e 's,.*selinux-policy-\\([^/]*\\)/.*,\\1,' /usr/share/selinux/devel/policyhelp 2>/dev/null)}
%if "%{_selinux_policy_version}" != ""
Requires:      selinux-policy >= %{_selinux_policy_version}
%endif


Requires(post):   /usr/sbin/semodule, /sbin/restorecon, /sbin/fixfiles, %{name}
Requires(postun): /usr/sbin/semodule, /sbin/restorecon, /sbin/fixfiles, %{name}


%global selinux_types %(%{__awk} '/^#[[:space:]]*SELINUXTYPE=/,/^[^#]/ { if ($3 == "-") printf "%s ", $2 }' /etc/selinux/config 2>/dev/null)
%global selinux_variants %([ -z "%{selinux_types}" ] && echo mls targeted || echo %{selinux_types})



%description
"Auth MemCookie" is an Apache v2.4 Authentication module based on "cookie" 
Authentication mechanism.

The module doesn’t make Authentication by it self, but verify if 
Authentication "the cookie" is valid for each url protected by the module.

Authentication is made externally by an Authentication html form page and all 
Authentication information necessary to the module a stored in memcached 
identified by the cookie value "Authentication session id" by this login page.

%prep
%setup -q -n apache2-%{name}-%{version}
mkdir SELinux
cp %{name}.te SELinux/

%build
make
#apxs -a -c %{name}.c

cd SELinux
for selinuxvariant in %{selinux_variants}
do
  make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile
  mv %{name}.pp %{name}.pp.${selinuxvariant}
  make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile clean
done
cd -

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_libdir}/httpd/modules
install -m 755 .libs/%{name}.so $RPM_BUILD_ROOT%{_libdir}/httpd/modules

for selinuxvariant in %{selinux_variants}
do
  install -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
  install -p -m 644 SELinux/%{name}.pp.${selinuxvariant} \
    %{buildroot}%{_datadir}/selinux/${selinuxvariant}/%{name}.pp
done

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc ChangeLog  LICENSE  README.md
%{_libdir}/httpd/modules/*.so

%doc SELinux/*
%{_datadir}/selinux/*/%{name}.pp

%post
for selinuxvariant in %{selinux_variants}
do
  /usr/sbin/semodule -s ${selinuxvariant} -i \
    %{_datadir}/selinux/${selinuxvariant}/%{name}.pp &> /dev/null || :
done
/sbin/fixfiles -R %{name} restore || :
/sbin/restorecon -R %{_localstatedir}/cache/%{name} || :

%postun
if [ $1 -eq 0 ] ; then
  for selinuxvariant in %{selinux_variants}
  do
    /usr/sbin/semodule -s ${selinuxvariant} -r %{name} &> /dev/null || :
  done
  /sbin/fixfiles -R myapp restore || :
  [ -d %{_localstatedir}/cache/myapp ]  && \
    /sbin/restorecon -R %{_localstatedir}/cache/%{name} &> /dev/null || :
fi

%changelog
* Wed Dec 18 2013 Tiago Batista <a19944+mod_auth_memcookie@gmail.com> 1.0.3-2
- Include an SELinux module in the package

* Mon Dec 2 2013 Tiago Batista  <a19944+mod_auth_memcookie@gmail.com> 1.0.3-1
- Initial RPM release


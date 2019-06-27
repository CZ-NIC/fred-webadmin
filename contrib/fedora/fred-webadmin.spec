%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$!!g')

Name:           fred-webadmin
Version:        %{our_version}
Release:        %{?our_release}%{!?our_release:1}%{?dist}
Summary:        Admin Interface for FRED (Fast Registry for Enum and Domains)
Group:          Applications/Utils
License:        GPL
URL:            http://fred.nic.cz
Source0:        %{name}-%{version}.tar.gz
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-%(%{__id_u} -n)
BuildRequires: python-setuptools gettext systemd 
Requires: fred-pylogger fred-idl python-ldap python-simplejson python-dns python-cherrypy python-omniORB omniORB-devel omniORB-servers redhat-lsb

%description
FRED (Free Registry for Enum and Domain) is free registry system for managing domain registrations. This package contains web administration application

%prep
%setup -n %{name}-%{version}

%install
python2 setup.py install -cO2 --force --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES --prefix=/usr

mkdir -p $RPM_BUILD_ROOT/%{_unitdir}
install contrib/fedora/fred-webadmin.service $RPM_BUILD_ROOT/%{_unitdir}

mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/fred/
install contrib/fedora/webadmin_cfg.py $RPM_BUILD_ROOT/%{_sysconfdir}/fred/

mkdir -p $RPM_BUILD_ROOT/%{_localstatedir}/log/fred-webadmin/
mkdir -p $RPM_BUILD_ROOT/%{_localstatedir}/lib/fred-webadmin/
mkdir -p $RPM_BUILD_ROOT/%{_localstatedir}/lib/fred-webadmin/sessions/

%pre
/usr/bin/getent passwd fred || /usr/sbin/useradd -r -d /etc/fred -s /bin/bash fred

%post
chown fred.fred %{_localstatedir}/log/fred-webadmin/
chown -R fred.fred %{_localstatedir}/lib/fred-webadmin/

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
%{_unitdir}/*
%config %{_sysconfdir}/fred/webadmin_cfg.py
%{_localstatedir}/log/fred-webadmin/
%{_localstatedir}/lib/fred-webadmin/
%{_localstatedir}/lib/fred-webadmin/sessions/

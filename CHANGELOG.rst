ChangeLog
=========

3.25.6 (2022-03-01)
-------------------

* Fix rpm build
* Fix CI
* Fix deprecated code from pylogger
* Rename changelog to CHANGELOG.rst to match all FRED projects

3.25.5 (2020-01-31)
-------------------

* Fix rpm for RHEL8 and F31

3.25.4 (2019-11-20)
-------------------

* Fix registrar update error messages
* Update spec file for F31 and Centos/RHEL 8

3.25.3 (2019-07-15)
-------------------

* Fix timezone conversion

3.25.2 (2019-06-27)
-------------------

* Fix rpm build

3.25.1 (2019-06-13)
-------------------

* Fix rpm build

3.25.0 (2019-03-20)
-------------------

* License GNU GPLv3+
* Use setuptools for distribution

3.24.1 (2019-02-11)
-------------------

* Add systemd service for fedora package

3.24.0 (2018-08-17)
-------------------

* Remove bank payments (statements)
* Public request - status enum renaming

3.23.0 (2018-04-20)
-------------------

* Remove no longer used date/time structs
* Fix timezone conversions (configuration)

3.22.0 (2018-03-14)
-------------------

* Switch to new common date/time and buffer data types in idl

3.21.0 (2018-03-08)
-------------------

* Adapt to mail_archive changes (get e-mail detail by pyfred-mailer renderMail method)
* Use statically compiled IDL modules
* Add registry record statement generation
* CSS style lint fixes

3.20.0 (2018-01-09)
-------------------

* Do not log registrar passwords to logger module

3.19.1 (2017-09-11)
-------------------

* Add sorting of Logger services

3.19.0 (2017-03-24)
-------------------

* button 'domains all' in domain detail also filters tech-c of associated keyset and nsset
* fix unicode error in error message (csv import of custom e-mail notification about domain going outzone)
* fix generated javascript content type (doesn't work with X-Content-Type-Options 'nosniff')
* removed cherrypy server from tests

3.18.0 (2017-03-02)
-------------------

* Add CI configuration
* Linter CSS
* Fedora packaging

3.17.0 (2016-11-22)
-------------------

* import csv form for custom e-mail notification about domain going outzone (after expiration)
* negative permissions for object fields (to hide values of specific attributes)
* tests - migration to twill-2.0 (Cito@github)
* fix - registrar update form (leap year, corba decoder bugs)
* fix - registrar unblock link

3.16.2 (2016-06-13)
-------------------

* fix - sort request types by name (alphabetically)

3.16.1 (2016-03-29)
-------------------

* patch corba recoder for omniorb 4.2.0

3.16.0 (2016-02-16)
-------------------

* admin. contact verification - sort table in resolving status

3.15.0 (2015-05-20)
-------------------

* add destination account number to payment detail page
* mailing address has same layout as permanent address
* separate permission for public request message resending
* fix - show contact identification type on detail page
* fix - appropriate error message when processing public request which has been already processed
* fix - public request processing confirmation message content
* fix - add explanatory note for admin. verification check status in list  view

3.14.1 (2015-02-12)
-------------------

* admin. contact verification fixes - contact check detail

  * with changed data
  * for deleted contact

3.14.0 (2014-10-17)
-------------------

* additional addreses at contact detail page
* ldap ssl support
* contact verification enhancements

3.13.2 (2014-10-02)
-------------------

* fix pin2/pin3 message resending

3.13.1 (2014-08-01)
-------------------

* fix memcached dependency
* add tests for admin. contact verification

3.13.0 (2014-06-12)
-------------------

* admin. contact verification impl.
* fix logger filter - server / request_type

3.12.0 (2014-02-13)
-------------------

* pin2 and pin3 buttons for message resending in public request details

3.11.0 (2013-11-06)
-------------------

* administrative blocking/unblocking domains (and holders)
* add logger request object reference filter (also add mojeid action button to contact detail)
* fix contact email filter is now case-insensitive
* fix login form - clear password field on error input

3.10.1 (2013-07-29)
-------------------

* Fix fedora rpm package build

3.10.0 (2013-04-03)
-------------------

* setup.py changes for new freddist
* CherryPy 3.2 ready
* Fix tests
* Add configurable pagetable row limit (defaults + per pagetable override)

3.9.5 (2012-11-21)
------------------

* Add autofocus to username input field at login screen
* Fix internal error when loading pagetable result with no filter set in backend
* Fix tests

3.9.4 (2012-10-18)
------------------

* Fix installation of additional directories

3.9.3 (2012-09-07)
------------------

* Whitespace normalization and PEP8-ification
* Update due to distutils changes (setup.cfg)

3.9.0 (2012-05-14)
------------------

* fixes - request_id history links (id=0)
* logger - filter property names list - select field

3.8.0 (2012-04-27)
------------------

* epp actions removed from fred

3.7.1 (2011-12-23)
------------------

* Links to actions switched to request logger

3.7.0 (2011-10-17)
------------------

* Registrar unblocking functionality impl.
* Fixed wrong result code for successfull operation in BankPaymentDetail
* Removed BankPayment InvoiceId filter
* Local distfred removed
* Simple filter tests
* Removed unused code
* Unused nicauth support temporarily disabled

3.6.0 (2011-01-24)
------------------

* Added timeout functionality in filters, the timeout is configurable
* Added filter for Destination Account, AccountMemo and CRTime in BankStatementFilter
* Added object references and result to LogRequest detail

3.5.4 (2010-10-24)
------------------

* Fixing unicode

3.5.2 (2010-10-23)
-------------------

* Showing messages again

3.5.1 (2010-10-18)
------------------

* Temporary disabling message display

3.5.0 (2010-10-18)
------------------

* Support for listing messages
* Implemented refactored logging interface

3.4.5 (2010-08-11)
------------------

* Change of registrar country attribute fixed
* Username attribute added to Logger request deatil

3.4.4 (2010-08-06)
------------------

* Logger filters for object's handle fixed (property name)

3.4.3 (2010-07-22)
------------------

* Keyset detail display fix
* Enhance permissions granularity (initial version)
* Typo fixes

3.4.2 (2010-07-02)
------------------

* Registrar edit form fix (system registrar bug)

3.4.1 (2010-07-02)
------------------

* Publish flag in domain detail

3.4.0 (2010-06-28)
------------------

* NSSet detail - report level field added
* Registrar edit form facelift (hideable sections).
* Added support for registrar certifications.
* Registrars can now be assigned to groups.
* Added registrar groups editor (creating/deleting/renaming groups).
* Logging only changes in registrar editation.
* Added group filter to registrar filter form.
* Added "next/prev." links to filter form page (briefly - if there is a time field with an offset
  (e.g. last month) displayed, this links jump to the results for the prev./next time period).
* Buttons in Dahne detail pages that jump directly to filter forms now only return results for the last month.
* Known bugs fixed.
* New unit tests added.

3.3.6 (2010-04-07)
------------------

* Introduced permissions checking (permissions are described using in csv file).
* Added an example csv file with user "test" having all the permissions.
* Minor bugfixes, mostly related to permissions.
* Changes in payment pairing / type assigning.
* Bugfixes.

3.3.5 (2010-03-23)
------------------

* Changes in payments (an unassigned payment is now recognized by having type == 1, not invoiceId == 0).

3.3.4 (2010-03-19)
------------------

* import order fix (CosNaming, omniORB)

3.3.3 (2010-03-17)
------------------

* Fixed bugs related to CORBA logd not available in omninames service / logd server not running / logd server crashing.
* Renamed BankStatements filter header to Payments.
* Fixed a bug, where KeySetDetail crashed sometimes when history was on.
* Fixed a bug, where we were hiding the whole log menu when CORBA logd was not available.

3.3.2 (2010-03-05)
------------------

* Choosing LDAP as auth method caused Daphne to crash at startup. Fixed.

3.3.1 (2010-03-03)
------------------

* Refactored adif.py (mostly login and authentication code).
* Added new unit tests, refactored old ones to reflect changes.
* Fixed the bug at login time (log_req variable not initialized).

3.3.0 (2010-02-19)
------------------

* Audit (Logger) component integration
* New tests added
* Fixed domain detail - display temporary contacts
* Bugfixes

3.1.6 (2009-07-02)
------------------

* Fixing default listening host in template config file

3.1.5 (2009-06-30)
------------------

* Adding possibility to set serverInZoneManual state on domain
* Support for Python 2.6
* Fixing startup script

3.1.4 (2009-05-25)
------------------

* Changed email fields in filter so that wildecards can be user
* Updated init script

3.1.3 (2009-03-26)
------------------

* In pagetable export to csv, separator have changed to ',' (from '|'),
  and changed to use standard python csv module.

3.1.2 (2009-02-04)
------------------

* Bugfix in mousover on history status field of objects
* Log directory changed to /var/log/fred-webadmin/
* Setup.py install script allows to specify LDAP directory
* Bugfix redirect after successful login (double login)
* Initial permissions framework (not used yet)

3.1.1 (2008-11-11)
------------------

* Adding possibility to edit registra system flag
* Bugfix of message in case of LDAP connection problems
* Updated MANIFEST.in

3.1.0 (2008-10-18)
------------------

* Adding DNSKEY record to keyset details

3.0.4 (2008-10-15)
------------------

* Fixing search for domains by admin contact
* Fixing invoicing
* no PDF and XML icons in invoice list when there are no PDF and XML
* PDF and XML links back in invoice details
* Fixing public request detail
* buttons formatting
* buttons hiding after request processing

3.0.3 (2008-10-02)
------------------

* Fixing CSV and TXT export

3.0.2 (2008-09-28)
------------------

* Fixing colors in disclosed elements

3.0.1 (2008-09-26)
------------------

* Filters can be modified
* Refactoring of display for disclose fields (with history)
* Displaying status of all types of objects and filter according to status

3.0.0 (2008-08-15)
------------------

* Adding KeySet object searching and details
* All object details contain history changes

2.2.0 (2008-07-10)
------------------

* release

2.1.0 (2008-06-24)
------------------

* release

2008-06-24
----------

* few bugfixes in installation process

2008-06-20
----------

* added filtr for ID into public requests
* added lists for mails, invoices and files
* added filtr for outzone date end cancel date into domains
* lot's of internal refactoring

2.0.1 (2008-06-05)
------------------

* small build system fixes
* release (2.0.1)

2.0.0 (2008-05-30)
------------------

* initial release

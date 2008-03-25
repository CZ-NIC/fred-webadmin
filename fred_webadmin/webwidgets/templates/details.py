#!/usr/bin/python
# -*- coding: utf-8 -*-

from fred_webadmin.webwidgets.gpyweb.gpyweb import attr, div, span, h2, table, tbody, tr, th, td, p, strong, b, small, a, form, input, select, option, textarea, script, pre, br, acronym
from fred_webadmin.webwidgets.adifwidgets import FilterPanel
from fred_webadmin.translation import _
from fred_webadmin.mappings import f_urls, f_objectType_name

class DetailDiv(div):
    def __init__(self, context):
        super(DetailDiv, self).__init__()
        self.media_files = ['/css/details.css']
        self.cssc = 'object_detail'
        self.tag = 'div'
        

class ContactDetailDiv(DetailDiv):
    def __init__(self, context):
        super(ContactDetailDiv, self).__init__(context)
        c = context
        result = c['result']
        self.add(
            table(attr(border='1', style='width: 96%'),
                  tr(th(attr(style='width: 180px'), _('Handle')), 
                     td(strong(span(result.handle)), span(attr(cssc='epp'), small('(EPP id:', span(result.roid, 'epp id'), ')'))), 
                     th('Status')),
                  tr(th(_('Name')), 
                     td(div(attr(cssc='disclose' + str(result.discloseName)), result.name)), 
                     td(attr(rowspan='10', valign='top', style='width: 90px'),
                        form(select(attr(size='12', cssc='disabled', disabled='disabled'), option('inactive'), option('clientDeleteProhibited'), option('serverDeleteProhibited'), option('clientHold'), option('serverHold'), option('clientRenewProhibited'), option('serverRenewProhibited'), option('clientTransferProhibited'), option('serverTransferProhibited'), option('clientUpdateProhibited'), option('serverUpdateProhibited'))))),
#                  tr(th(_('Cancel_date')), 
#                     td(result.cancelDate)),
                  tr(th(_('SSN')), 
                     td(result.ssn)),
                  tr(th(_('Organization')), 
                     td(div(attr(cssc='disclose' + str(result.discloseOrganization)), div(result.organization)))),
                  tr(th(_('VAT')), 
                     td(result.vat)),
                  tr(th(_('Telephone')), 
                     td(div(attr(cssc='disclose' + str(result.discloseTelephone)), div(result.telephone)))),
                  tr(th(_('Fax')), 
                     td(div(attr(cssc='disclose' + str(result.discloseFax)), div(result.fax)))),
                  tr(th(_('Email')), 
                     td(div(attr(cssc='disclose' + str(result.discloseEmail)), div(a(attr(href='mailto:' + result.email), result.email))))),
                  tr(th(_('Notify_email')), 
                     td(a(attr(href='mailto' + result.notifyEmail), result.notifyEmail))),
                  tr(th(_('Auth_info')), 
                     td(span(result.authInfo)))),

            table(attr(border='1', style='width: 96%'),
                  tr(th(attr(style='width: 180px'), _('Create_date')), 
                     td(span(result.createDate)), 
                     th(attr(style='width: 120px'), _('by_registrar:')), 
                     td(attr(style='width: 280px'), a(attr(href=f_urls['registrars'] + 'detail/?handle=' + result.createRegistrarHandle), result.registrarHandle))),
                  tr(th(_('Last_update_date:')), 
                     td(span(result.updateDate)), 
                     th(_('by_registrar:')), 
                     td(a(attr(href=f_urls['registrars'] + 'detail/?handle=' + result.updateRegistrarHandle), result.updateRegistrarHandle))),
#                  tr(th(attr(style='width: 180px'), _('Cancel_date:')), 
#                     td(attr(colspan='3'), span(result.cancelDate)))
                 ),
            
            table(attr(border='1', style='width: 96%'),
                  tr(th(attr(style='width: 180px'), _('Address')), 
                     td(div(attr(cssc='disclose' + str(result.discloseAddress)), div(result.street1), div(result.street2), div(result.street3)))),
                  tr(th(_('ZIP')), 
                     td(span(result.postalcode))),
                  tr(th(_('City')), 
                     td(span(result.city))),
                  tr(th(_('Country')), 
                     td(span(result.country))))
        )
        
        if c.get('edit'):
            self.add(p(input(attr(type='submit', value=':Save:')), input(attr(type='reset', value=':Renew:'))))
        else:
            self.add(FilterPanel([
                [_('Domains_owner'), 'domains', [{'registrant.handle': result.handle}]],
                [_('Domains_admin'), 'domains', [{'adminContact.handle': result.handle}]],
                [_('Domains_all'), 'domains', [{'registrant.handle': result.handle}, {'adminContact.handle': result.handle}]],
                [_('NSSets'), 'nssets', [{'admin.handle': result.handle}]],
                [_('Requests'), 'actions', [{'object.handle': result.handle}]],
                [_('Emails'), 'mails', [{'object.handle': result.handle}]],
            ]))
            
        

class DomainDetailDiv(DetailDiv):
    def __init__(self, context):
        super(DomainDetailDiv, self).__init__(context)
        c = context
        result = c['result']
        self.add(
            table(attr(border='1', style='width: 96%'), 
                  tr(th(attr(style='width: 180px'), _('Domain')), 
                     td(strong(span(result.fqdn)), span(attr(cssc='epp'), small('(EPP id:', span(result.roid), ')'))), 
                     th(_('Status'))), 
                  tr(th(_('Registration_date')), 
                     td(span(result.createDate)), 
                     td(attr(rowspan='7', valign='top', style='width: 90px'), form(select(attr(size='8', cssc='disabled', disabled='disabled'), option('inactive'), option('clientDeleteProhibited'), option('serverDeleteProhibited'), option('clientHold'), option('serverHold'), option('clientRenewProhibited'), option('serverRenewProhibited'), option('clientTransferProhibited'), option('serverTransferProhibited'), option('clientUpdateProhibited'), option('serverUpdateProhibited'))))), 
                  tr(th(_('Expiry_date')), 
                     td(span(result.expirationDate))), 
#                  tr(th(_('Deleted_date')), 
#                     td(span(''))), 
#                  tr(th(_('Cancel_date')), 
#                     td(span(''))), 
                  tr(th(_('Validation_date')), 
                     td(span(result.valExDate))), 
                  tr(th(_('Notify_email')), 
                     td(span('default'))), 
                  tr(th(_('Auth_info')), 
                     td(span(result.authInfo)))),

            table(attr(border='1', style='width: 96%'), 
                  tr(th(attr(colspan='2'), _('Owner'))), 
                  tr(th(attr(style='width: 180px'), _('Handle')), 
                     td(a(attr(href=f_urls['contacts'] + 'detail/?handle=' + result.registrant.handle), result.registrant.handle))), 
                  tr(th(_('Name')),
                     td(span(result.registrant.name))), 
                  tr(th(_('Address')), 
                     td(div(result.registrant.street1), div(result.registrant.street2), div(result.registrant.street3), div(result.registrant.postalcode), div(result.registrant.city), div(result.registrant.country)))),
        )
        
        #admins:
        admins_table = table(attr(border='1', style='width: 96%'), 
                             tr(th(attr(colspan='4'), _('Administrative_contacts')))
                            )
        for admin in result.admins:
            admins_table.add(
                  tr(th(attr(style='width: 180px'), _('Handle')), 
                     td(a(attr(href=f_urls['contacts'] + 'detail/?handle=' + admin.handle), admin.handle)), 
                     th(_('Email')), 
                     td(a(attr(href='mailto:' + admin.email), admin.email)))
            )
        self.add(admins_table)
        
        #temps:
        temps_table = table(attr(border='1', style='width: 96%'), 
                            tr(th(attr(colspan='4'), _('Temporary_contacts'))),
                           )
        for admin in result.temps:
            temps_table.add(
                  tr(th(attr(style='width: 180px'), _('Handle')), 
                     td(a(attr(href=f_urls['contacts'] + 'detail/?handle=' + admin.handle), admin.handle)), 
                     th(_('Email')), 
                     td(a(attr(href='mailto:' + admin.email), admin.email)))
            )
        self.add(temps_table)
        
        if result.nsset:
            #nsets:
            nssets_table = table(attr(border='1', style=('width: 96%')), 
                                tr(th(attr(colspan='4'), _('NSSet'))), 
                                tr(th(attr(style='180px'), _('Handle')), 
                                   td(attr(colspan='3'), a(attr(href=f_urls['nssets'] + 'detail/?handle=' + result.nssetHandle), result.nssetHandle))), 
                                tr(th(_('Registrar')), 
                                   td(attr(colspan='3'), a(attr(href=f_urls['registrars'] + 'detail/?handle=' + result.nsset.registrarHandle), result.nsset.registrarHandle)))
                                )
            #  nsset-admins (tech-contacts)
            for i, admin in enumerate(result.nsset.admins):
                nssets_table.add(
                      tr(th(attr(style='width: 180px'), 'Tech-ID/' + str(i + 1)), 
                         td(a(attr(href=f_urls['contacts'] + 'detail/?handle=' + admin.handle), admin.handle, 'TECH-ID')), 
                         th(_('Email')), 
                         td(a(attr(href='mailto:' + admin.email), admin.email)))
                )
            # nsset-hosts
            for i, host in enumerate(result.nsset.hosts):
                ips = td()
                for ip in host.inet:
                    ips.add(div(ip))
                nssets_table.add(
                      tr(th('DNS/' + str(i + 1)), 
                         td(host.fqdn), 
                         th(_('IPs')), 
                         ips)
                )
            self.add(nssets_table)
        
        if result.registrar:
            self.add(
                table(attr(border='1', style='width: 96%'), 
                      tr(th(attr(style='width: 180px'), _('Selected_registrar')), 
                         th(attr(style='width: 250px'), _('Handle')), 
                         th(_('from'))), 
                      tr(td(result.registrar.name), 
                         td(a(attr(href=f_urls['registrars'] + 'detail/?handle=' + result.registrarHandle), result.registrarHandle)), 
                         td(result.updateDate)))
            )
        if result.createRegistrar:
            self.add(
                table(attr(border='1', style='width: 96%'), 
                      tr(th(attr(style='width: 180px'), _('Creating_registrar')), 
                         th(attr(style='width: 250px'), _('handle')), 
                         th(_('from'))), 
                      tr(td(result.createRegistrar.name), 
                         td(a(attr(href=f_urls['registrars'] + 'detail/?handle=' + result.createRegistrarHandle), result.createRegistrarHandle), 
                         td(result.createDate))))
            )
        if result.updateRegistrar:
            self.add(
                table(attr(border='1', style='width: 96%'), 
                      tr(th(attr(style='width: 180px'), _('Last_update_registrar')), 
                         th(attr(style='width: 250px'), _('handle')), 
                         th(_('Date'))), 
                      tr(td(result.updateRegistrar.name), 
                         td(a(attr(href=f_urls['registrars'] + 'detail/?handle=' + result.updateRegistrarHandle), result.updateRegistrarHandle)), 
                         td(result.updateDate)))
            )
            
            self.add(FilterPanel([
                [_('Requests'), 'actions', [{'object.handle': result.fqdn}]],
                [_('Emails'), 'mails', [{'object.handle': result.fqdn}]],
                [_('dig'), f_urls['domains'] + 'dig/?handle=' + result.fqdn]
            ]))
        
class NSSetDetailDiv(DetailDiv):
    def __init__(self, context):
        super(NSSetDetailDiv, self).__init__(context)
        c = context
        result = c['result']
        
    
        nsset_table = table(attr(style='width: 96%', border='1'), 
            tr(th(attr(style='width: 180px'), _('Handle')), 
               td(attr(colspan='3'), strong(span(result.handle)), span(attr(cssc='epp'), small('(EPP id:', span(result.roid, 'epp id'), ')')))),
            tr(th(_('Registrar')), 
               td(attr(colspan='3'), a(attr(href=f_urls['registrars'] + 'detail/?handle=' + result.registrar.handle), result.registrar.handle))),
            tr(th(_('Auth_info')), 
               td(attr(colspan='3'), span(result.authInfo)))
        )
        
        for i, admin in enumerate(result.admins): 
            nsset_table.add(
                tr(th(attr(style='width: 180px'), 'Tech-ID/' + str(i+1)), 
                   td(a(attr(href=f_urls['contacts'] + 'detail/?handle=' + admin.handle), admin.handle)), 
                   th(_('Email')), 
                   td(a(attr(href='mailto:' + admin.email), admin.email)))
            )
        for i, host in enumerate(result.hosts):
            nsset_table.add(
                tr(th('DNS/' + str(i+1)), 
                   td(host.fqdn), 
                   th(_('IPs')), 
                   td(div([div(ip) for ip in host.inet])))
            )
        
        self.add(
            nsset_table,
            table(attr(border='1', style='width: 96%'), 
                  tbody(tr(th(attr(style='width: 180px'), _('Create_date')), 
                           td(attr(colspan='3'), span(result.createDate)), 
                           th(attr(style='width: 120px'), _('by_registrar:')), 
                           td(attr(style='width: 280px'), a(attr(href=f_urls['registrars'] + 'detail/?handle=' + result.createRegistrarHandle), result.registrarHandle))),
                        tr(th(_('Last_update_date')), 
                           td(attr(colspan='3'), span(result.updateDate)), 
                           th(_('by_registrar:')), 
                           td(a(attr(href=f_urls['registrars'] + 'detail/?handle=' + result.updateRegistrarHandle), result.updateRegistrarHandle))),
                        tr(th(_('Last_transfer_date:')), 
                           td(attr(colspan='5'), span(result.transferDate))))),
            
        )
        self.add(FilterPanel([
            [_('Domains'), 'domains', [{'nSSet.handle': result.handle}]],
            [_('Requests'), 'actions', [{'object.handle': result.handle}]],
            [_('Emails'), 'mails', [{'object.handle': result.handle}]],
        ]))

class ActionDetailDiv(DetailDiv):
    def __init__(self, context):
        super(ActionDetailDiv, self).__init__(context)
        c = context
        result = c['result']
        self.media_files.extend(('/js/shCore.js', '/js/shBrushXml.js', '/css/SyntaxHighlighter.css'))
        self.add(
            h2(_('Request_information')),
            table(attr(style='width: 96%', border='1'), 
                  tr(th(attr(style='width: 180px'), _('Received_date')), 
                     td(strong(span(result.time)))), 
                  tr(th(_('Registrar')), 
                     td(a(attr(href=f_urls['registrars'] + 'detail/?handle=' + result.registrar.handle), result.registrar.handle))), 
                  tr(th(_('objectHandle')), 
                     td(span(result.objectHandle))), 
                  tr(th(_('Type')), 
                     td(span(result.type))), 
                  tr(th(_('Result')), 
                     td(span(result.result))), 
                  tr(th(_('clTRID')), 
                     td(span(result.clTRID))), 
                  tr(th(_('svTRID')), 
                     td(span(result.svTRID)))),

            table(attr(border='1', style='width: 96%'), 
                  tr(th(_('XML'))), 
                  tr(td(textarea(attr(name='code', cssc='xml', rows='40'), result.xml)))),
            script(attr(type='text/javascript'), "dp.SyntaxHighlighter.HighlightAll('code');")
        )
        

class RegistrarDetailDiv(DetailDiv):
    def __init__(self, context):
        super(RegistrarDetailDiv, self).__init__(context)
        c = context
        result = c['result']
        if c.get('edit'):
            self.media_files.append('/js/edit.js')
        self.add(h2(_('Detail_of_registrar')))
        
        self.add(table(attr(style='width: 96%', border='1'), 
            tr(th(attr(style='width: 180px'), _('Type')), 
                 td(span(result.handle))), 
            tr(th(_('Name')), 
               td(span(result.name))), 
            tr(th(_('Organization')), 
               td(span(result.organization))), 
            tr(th(_('Current_reminder')), 
               td(span(result.credit)))
        ))
        self.add(table(attr(width='96%', border='1'),
            tr(th(attr(colspan='2'), strong(_('Address')))),
            tr(th(attr(style='width: 180px'), _('Street')+'1'), 
               td(span(result.street1))), 
            tr(th(_('Street')+'2'), 
               td(span(result.street2))),
            tr(th(_('Street')+'3'), 
               td(span(result.street3))),
            tr(th(_('City')), 
               td(span(result.city))),
            tr(th(_('ZIP')), 
               td(span(result.postalcode))),
            tr(th(_('State')), 
               td(span(result.stateorprovince))),
            tr(th(_('Country')), 
               td(span(result.country))),
        ))
            
        self.add(table(attr(width='96%', border='1'),
            tr(th(attr(colspan='2'), strong(_('Other_data')))),
            tr(th(attr(style='width: 180px'), _('Telephone')), 
               td(span(result.telephone))),
            tr(th(_('Fax')), 
               td(span(result.fax))),
            tr(th(_('Email')), 
               td(span(a(attr(href='mailto:' + result.email), result.email)))),
            tr(th(_('URL')), 
               td(span(result.url)))
        ))
        
        auth_table = table(attr(style='width: 96%', border='1', id='certContainer'),
                           tr(th(_('Authentication'))))
        for acc in result.access:
            auth_table.add(
                tr(td(table(attr(cssc="certGroup"), 
                            tr(th(attr(style='width: 180px'), _('Password')),
                               td(span(acc.password))),
                            tr(th(attr(style='width: 180'), _('MD5_of_certificate')),
                               td(span(attr(cssc="certString"), acc.md5Cert)))
                  )))
            )
        self.add(auth_table)

        self.add(FilterPanel([
            [_('Domains_selected'), 'domains', [{'registrar.handle': result.handle}]],
            [_('Domains_creating'), 'domains', [{'createRegistrar.handle': result.handle}]],
            [_('Contacts'), 'contacts', [{'registrar.handle': result.handle}]],
            [_('Requests'), 'actions', [{'registrar.handle': result.handle}]],
            [_('Emails'), 'mails', [{'object.registrar.handle': result.handle}]],
        ]))

class AuthInfoDetailDiv(DetailDiv):
    def __init__(self, context):
        super(AuthInfoDetailDiv, self).__init__(context)
        c = context
        result = c['result']
        self.media_files.append('/js/edit.js')
        
        self.add(
            h2(_('AuthInfo_detail')),
            
            table(attr(border='1', style='width: 96%'), 
                  tr(th(attr(style='width=180px'), _('Handle')), 
                     td(attr(), strong(a(attr(href=f_urls[f_objectType_name[result.oType]] + '/detail/?handle=' + result.handle), result.handle)))), 
                  tr(th(_('Reason')), 
                     td(result.reason)), 
                  tr(th(_('Request_type')), 
                     td(result.type)), 
                  tr(th(_('Status')), 
                     td(result.status)), 
                  tr(th(_('Registrar')), 
                     td(a(attr(href=f_urls['registrars'] + 'detail/?handle=' + result.registrar), result.registrar))), 
                  tr(th(_('svTRID')), 
                     td(a(attr(href=f_urls['actions'] + 'detail/?svTRID=' + result.svTRID), result.svTRID))), 
                  tr(th(_('Reply_Email')), 
                     td(a(attr(href='mailto:' + result.email), result.email))), 
                  tr(th(_('Email')),
                     ['', td(a(attr(href=f_urls['mails'] + 'detail/?id=' + str(result.answerEmailId)), result.answerEmailId))][bool(result.answerEmailId)]), 
                  tr(th(_('Create_time')), 
                     td(result.crTime)), 
                  tr(th(_('Close_time')), 
                     td(result.closeTime)))
        )
        if not result.closeTime:
            self.add(
                table(attr(style='width: 96%', border='1'), tr(th(attr(colspan='5'), b(_('Options')))), 
                      tr(td(form(attr(id='processAuthInfo', action=f_urls['authinfo'] + 'resolve/', method='POST'),
                                 input(attr(type='hidden', name='id', value=result.id)), 
                                 input(attr(type='button', value=_('Accept_and_send'), onclick='processAuthInfo(this); return false;')))), 
                         td(form(attr(id='closeAuthInfo', action=f_urls['authinfo'] + 'close/', method='POST'),
                                 input(attr(type='hidden', name='id', value=result.id)), 
                                 input(attr(type='button', value=_('Invalidate_and_close'), onclick='closeAuthInfo(this); return false;'))))))
    
            )
            self.add(FilterPanel([
                [_('Domains_selected'), 'domains', [{'registrar.handle': result.handle}]],
                [_('Domains_creating'), 'domains', [{'createRegistrar.handle': result.handle}]],
                [_('Contacts'), 'contacts', [{'registrar.handle': result.handle}]],
                [_('Requests'), 'actions', [{'registrar.handle': result.handle}]],
                [_('Emails'), 'mails', [{'object.registrar.handle': result.handle}]],
            ]))


class MailDetailDiv(DetailDiv):
    def __init__(self, context):
        super(MailDetailDiv, self).__init__(context)
        c = context
        result = c['result']
        handles = td()
        for handle in result.handle:
            if handle.type:
                div(a(attr(href=f_urls[handle.type] + 'detail/?handle=' + handle.handle), handle.handle), br())
            else:
                div(handle.handle, br())
        attachments = td()
        for attachment in result.attachmens:
            if attachment.id:
                div(a(attr(attachment.name, attr(href=f_urls['attachment'] + '?id=' + attachment.id))))
            else:
                div(attachment.name)
        self.add(
            h2(_('Detail_of_email')),
            table(attr(border='1', width='96%'), 
                  tr(th(attr(width='180'), _('Handles')),
                     handles),
                  tr(th(_('Status')), td(result.status)),
                  tr(th(_('Type')), td(result.type)), 
                  tr(th(_('Create_time')), td(result.createTime)), 
                  tr(th(_('Modify_time')), td(result.modTime)), 
                  tr(th(_('Attachments')), attachments)
            ), 
                  
            table(attr(border='1', width='96%'), 
                  tr(th(_('Email'))), 
                  tr(td(pre(attr(cssc='email'), result.content))))
        )
        
class InvoiceDetailDiv(DetailDiv):
    def __init__(self, context):
        super(InvoiceDetailDiv, self).__init__(context)
        c = context
        result = c['result']
        
        self.add(
            h2(_('Invoice_detail')),
            table(attr(border='1', width='96%'), 
                  tr(th(attr(width='180'), _('Number')), 
                     td(result.number)), 
                  tr(th(_('Registrar')), 
                     td(a(attr(href=f_urls['registrars'] + 'detail/?handle=' + result.registrarHandle), result.registrarHandle))), 
                  tr(th(_('Credit')), 
                     td(result.credit)), 
                  tr(th(_('Create_date')), 
                     td(span(result.crTime))), 
                  tr(th(_('Tax_date')), 
                     td(span(result.taxDate))), 
                  tr(th(_('From_date')), 
                     td(span(result.fromDate))), 
                  tr(th(_('To_date')), 
                     td(span(result.toDate))), 
                  tr(th(_('Type')), 
                     td(result.type)), 
                  tr(th(_('Price')), 
                     td(strong(result.price), small('string: (${here/result/total} + ${here/result/totalVAT} :of: ${here/result/vatRate}% :VAT:')))), 
                  tr(th(_('Variable_Symbol')), 
                     td(result.varSymbol)), 
                  
                  [tr(th(_('PDF')), 
                      td(a(attr(href=f_urls['attachments'] + '?id=${result.filePDF'), result.filePDFinfo.name), 
                         ', ' + _('size'), span(result.filePDFinfo.size), _('bytes, created'), span(result.filePDFinfo.crdate))), 
                   tr(th(_('PDF')), 
                      td('N/A')),
                  ][bool(result.filePDF)], 

                  [tr(th(_('XML')), 
                      td(a(attr(href='attachment/?id='+result.fileXML), _('size'), 
                           span(attr(result.fileXMLinfo.size)), _('bytes:, :created'), span(result.fileXMLinfo.crdate)))), 
                   tr(th(_('XML')), 
                      td('N/A'))][bool(result.fileXML)],

            table(attr(border='1', width='96%'), 
                  tr(th(attr(colspan='3'), b(_('Payments')))), 
                  ['',
                   tr(th('Number'), 
                      th('Price'), 
                      th('Balance')), 
                   [tr(td(a(attr(href=f_urls['invoices'] + 'detail/?id=' + item.id), item.number)), 
                       td(item.price), 
                       td(item.balance)) 
                    for item in result.payments
                   ]
                  ][bool(result.payments)]
            ),

            table(attr(border='1', width='96%'), tr(th(attr(colspan='7'), b(_('Actions')))), 
                  ['',
                   tr(
                     th('Object Name'), 
                     th('Action Time'), 
                     th('exDate'), 
                     th('Type'), 
                     th('Count'), 
                     th(acronym(attr(title=':Price_Per_Unit:'), _('PPU'))), 
                     th('Price')), 
                  [tr(
                     td(a(attr(TAL_attributes='href string: ${runtime/approot}domains/detail/?handle=${item/objectName}', TAL_content='item/objectName'))), 
                     td('item/actionTime'), 
                     td('item/exDate'), 
                     td('item/actionType'), 
                     td('item/unitsCount'), 
                     td('item/pricePerUnit'), 
                     td('item/price')) for item in result.actions
                  ]
                 ][not bool(result.actions)]
            )
        )

# regular expression for replacing TAL:

# attr\(TAL_content=([^,\)]*)\)
# $1


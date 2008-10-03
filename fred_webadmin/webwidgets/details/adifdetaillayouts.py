from fred_webadmin.webwidgets.details.detaillayouts import TableDetailLayout
from fred_webadmin.translation import _
from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget, tagid, attr, notag, div, span, table, caption, thead, tbody, tr, th, td, input, label, select, option, ul, li, script, a, img, strong

class DomainsNSSetDetailLayout(TableDetailLayout):
    def __init__(self, *content, **kwd):
        super(DomainsNSSetDetailLayout, self).__init__(*content, **kwd)
        self.cssc = 'section_table'
        
    def _render_nsset(self, nsset_detail):
        registrar_detail = nsset_detail.fields.get('registrar').current_field.inner_detail # registrar of nsset
        
        handle_field = nsset_detail.fields['handle_url']
        registrar_field = registrar_detail.fields['handle_url']
        admins_field = nsset_detail.fields['admins']
        hosts_field = nsset_detail.fields['hosts']
        
        handle_label = self.get_label_name(handle_field)
        registrar_label = self.get_label_name(_('Registrar'))
        admins_label = self.get_label_name(_('Tech. contacts'))
        hosts_label = self.get_label_name(_('DNSs'))
        
        self.add(tr(td(attr(cssc='left_label'), handle_label), td(handle_field)))
        self.add(tr(td(attr(cssc='left_label'), registrar_label), td(registrar_field)))
        
        for i, admin_detail in enumerate(admins_field.current_field.inner_details):
            row = tr()
            if i == 0:
                row.add(td(attr(cssc='left_label', rowspan=len(admins_field.current_field.inner_details)), 
                                admins_label))
            email_part = ''
            if admin_detail.fields['email'].value:
                email_part = [', ' , admin_detail.fields['email']] 
            row.add(td(attr(enclose_content=True), admin_detail.fields['handle_url'], email_part))
            self.add(row)
        
        for i, host_detail in enumerate(hosts_field.current_field.inner_details):
            row = tr()
            if i == 0:
                row.add(td(attr(cssc='left_label', rowspan=len(hosts_field.current_field.inner_details)), 
                           hosts_label))
            
            cell = td(attr(enclose_content=True))
            cell.add(host_detail.fields['fqdn'])

            if host_detail.fields['inet'].value:
                cell.add(' (', host_detail.fields['inet'], ')')

            row.add(cell)
            self.add(row)
        
    def create_layout(self):
        #if not self.detail.fields.get('nsset').displaying_history: # history is displayed only if history is on AND there is more than one history record in nsset historyRecordList
        nsset_detail = self.detail
        self._render_nsset(nsset_detail)



class DomainsKeySetDetailLayout(TableDetailLayout):
    def __init__(self, *content, **kwd):
        super(DomainsKeySetDetailLayout, self).__init__(*content, **kwd)
        self.cssc = 'section_table'
        
    def _render_keyset(self, keyset_detail):
        registrar_detail = keyset_detail.fields.get('registrar').current_field.inner_detail # registrar of keyset
        
        handle_field = keyset_detail.fields['handle_url']
        registrar_field = registrar_detail.fields['handle_url']
        admins_field = keyset_detail.fields['admins']
        dsrecords_field = keyset_detail.fields['dsrecords']
        dnskeys_field = keyset_detail.fields['dnskeys']
        
        handle_label = self.get_label_name(handle_field)
        registrar_label = self.get_label_name(_('Registrar'))
        admins_label = self.get_label_name(_('Tech. contacts'))
        dsrecords_label = self.get_label_name(_('DS records'))
        dnskeys_label = self.get_label_name(_('DNSKeys'))

        
        self.add(tr(td(attr(cssc='left_label'), handle_label), td(handle_field)))
        self.add(tr(td(attr(cssc='left_label'), registrar_label), td(registrar_field)))
        
        for i, admin_detail in enumerate(admins_field.current_field.inner_details):
            row = tr()
            if i == 0:
                row.add(td(attr(cssc='left_label', rowspan=len(admins_field.current_field.inner_details)), 
                                admins_label))
            email_part = ''
            if admin_detail.fields['email'].value:
                email_part = [', ' , admin_detail.fields['email']] 
            row.add(td(attr(enclose_content=True), admin_detail.fields['handle_url'], email_part))
            self.add(row)
        
        for i, dsrecord_detail in enumerate(dsrecords_field.current_field.inner_details):
            row = tr()
            if i == 0:
                row.add(td(attr(cssc='left_label', rowspan=len(dsrecords_field.current_field.inner_details)), 
                           dsrecords_label))
            
            cell = td(attr(enclose_content=True))
            cell.add(dsrecord_detail.fields['keyTag'])

            cell.add(dsrecord_detail.fields['digest'], ' (', dsrecord_detail.fields['digestType'],')')

            row.add(cell)
            self.add(row)

        for i, dnskey_detail in enumerate(dnskeys_field.current_field.inner_details):
            row = tr()
            if i == 0:
                row.add(td(attr(cssc='left_label', rowspan=len(dnskeys_field.current_field.inner_details)), 
                           dnskeys_label))
            
            cell = td(attr(enclose_content=True))
            #cell.add(dnskey_detail.fields['flags'])
            #cell.add(', ')
            cell.add(dnskey_detail.fields['key'])

            row.add(cell)
            self.add(row)
        
    def create_layout(self):
        keyset_detail = self.detail
        self._render_keyset(keyset_detail)

   

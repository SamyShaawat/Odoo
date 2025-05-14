/** @odoo-module **/

import { PosDB } from "@point_of_sale/app/store/db";
import { patch } from "@web/core/utils/patch";

patch(PosDB.prototype,{
    _partner_search_string: function(partner){
        var str =  partner.name || '';
        if(partner.customer_seq){
            str += '|' + partner.customer_seq;
        }
        if(partner.barcode){
            str += '|' + partner.barcode;
        }
        if(partner.address){
            str += '|' + partner.address;
        }
        if(partner.phone){
            str += '|' + partner.phone.split(' ').join('');
        }
        if(partner.mobile){
            str += '|' + partner.mobile.split(' ').join('');
        }
        if(partner.email){
            str += '|' + partner.email;
        }
        if(partner.vat){
            str += '|' + partner.vat;
        }
        str = '' + partner.id + ':' + str.replace(':', '').replace(/\n/g, ' ') + '\n';
        return str;
    },
});

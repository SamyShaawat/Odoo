odoo.define('commission_reports.commission_end_of_day_report', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var Context = require('web.Context');
var Dialog = require('web.Dialog');
var datepicker = require('web.datepicker');
var session = require('web.session');
var field_utils = require('web.field_utils');
var ReportWidget = require('stock.ReportWidget');
var framework = require('web.framework');
var { WarningDialog } = require("@web/legacy/js/_deprecated/crash_manager_warning_dialog");

var QWeb = core.qweb;
var _t = core._t;

var CommissionEndOfDayReport = AbstractAction.extend({
    hasControlPanel: true,

    events: {
        'click .js_report_commission_end_of_day_pdf': '_onPrintPdfBtnClicked',
        'click .js_report_commission_end_of_day_xlsx': '_onPrintXlsxBtnClicked',
    },

    // Stores all the parameters of the action.
    init: function(parent, action) {
        this.given_context = action.context;
        this.kwargs = {};
        return this._super.apply(this, arguments);
    },

    willStart: function() {
        return Promise.all([this._super.apply(this, arguments), this.get_html()]);
    },

    set_html: function() {
        var self = this;
        self.$('.o_content').html(this.html);
        self.renderButtons();
        self.renderSearchViewButtons();
        self.update_cp();
    },

    start: async function() {
        this.controlPanelProps.cp_content = { $buttons: this.$buttons, $searchview_buttons: this.$searchview_buttons };
        await this._super(...arguments);
        this.set_html();
    },

    // Fetches the html and is previous report.context if any, else create it
    get_html: async function() {
        const { html, options } = await this._rpc({
            args: [this.kwargs],
            method: 'get_html',
            model: 'commission.endof.day.report',
        });
        console.log(options);
        this.html = html;
        this.kwargs = options;
    },

    // Updates the control panel and render the elements that have yet to be rendered
    update_cp: function() {
        if (!this.$buttons) {
            this.renderButtons();
        }
        if (!this.$searchview_buttons) {
            this.renderSearchViewButtons();
        }
        this.controlPanelProps.cp_content = { $buttons: this.$buttons, $searchview_buttons:this.$searchview_buttons };
        return this.updateControlPanel();
    },

    renderButtons: function() {
        var self = this;
        this.$buttons = $(QWeb.render("commission_reports.commission_end_of_day_buttons", {}));
        return this.$buttons;
    },

    renderSearchViewButtons: function () {
        var self = this;
        this.$searchview_buttons = $(QWeb.render("commission_reports.commission_end_of_day_searchview_buttons", {options:this.kwargs}));

        // bind searchview buttons/filter to the correct actions
        var $datetimepickers = this.$searchview_buttons.find('.js_commission_reports_datetimepicker');
        var options = { // Set the options for the datetimepickers
            locale : moment.locale(),
            format : 'L',
            icons: {
                date: "fa fa-calendar",
            },
        };
        // attach datepicker
        $datetimepickers.each(function () {
            var name = $(this).find('input').attr('name');
            var defaultValue = $(this).data('default-value');
            $(this).datetimepicker(options);
            var dt = new datepicker.DateWidget(options);
            dt.replace($(this)).then(function () {
                dt.$el.find('input').attr('name', name);
                if (defaultValue) { // Set its default value if there is one
                    dt.setValue(moment(defaultValue));
                }
            });
        });
        // format date that needs to be show in user lang
        _.each(this.$searchview_buttons.find('.js_format_date'), function(dt) {
            var date_value = $(dt).html();
            $(dt).html((new moment(date_value)).format('ll'));
        });

        // click events
        this.$searchview_buttons.find('.js_commission_report_search_btn').click(function (event) {
            var error = false;
            var date_to = self.$searchview_buttons.find('.o_datepicker_input[name="date_to"]');
            if (date_to.length > 0){
                error = date_to.val() === ""
                self.kwargs.date_to = field_utils.parse.date(date_to.val());
            }
            if (error) {
                new WarningDialog(self, {
                    title: _t("Odoo Warning"),
                }, {
                    message: _t("Date cannot be empty")
                }).open();
            }

            // Reload
            self.reload();
        });

        return this.$searchview_buttons;
    },

    format_date: function(moment_date) {
        var date_format = 'YYYY-MM-DD';
        return moment_date.format(date_format);
    },

    _onPrintPdfBtnClicked: function (){
        var self = this;
        var vals = {
          "type": "ir_actions_commission_report_download",
          "data": {
            "model": "commission.endof.day.report",
            "output_format": "pdf",
            "report_name": "commission_end_of_day",
            "options": JSON.stringify(this.kwargs)
          }
        }
        var doActionProm = self.do_action(vals);
        return doActionProm;
    },

    _onPrintXlsxBtnClicked: function (){
        var self = this;
        var vals = {
          "type": "ir_actions_commission_report_download",
          "data": {
            "model": "commission.endof.day.report",
            "output_format": "xlsx",
            "report_name": "commission_end_of_day",
            "options": JSON.stringify(this.kwargs)
          }
        }
        var doActionProm = self.do_action(vals);
        return doActionProm;
    },

    reload: function() {
        var self = this;
        self.$('.o_content').empty();
        Promise.resolve(this.get_html()).then(function(){
            self.set_html();
        });
    },

    destroy: function () {
        this._super.apply(this, arguments);
    },
});

core.action_registry.add('commission_end_of_day_client', CommissionEndOfDayReport);

return CommissionEndOfDayReport;

});

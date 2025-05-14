/** @odoo-module **/

const {Component} = owl;

export class ActiveCallsTray extends Component {
    static template = 'asterisk_plus.active_calls_tray'
    _onClick() {
        this.props.bus.trigger('active_calls_toggle_display');
    }
}


/** @odoo-module **/
import {registry} from "@web/core/registry"
import {ActiveCallsTray} from "@asterisk_plus/components/active_calls/active_calls_tray"
import {ActiveCallsPopup} from "@asterisk_plus/components/active_calls/active_calls_popup"

const {EventBus} = owl

export const ActiveCallsService = {
    async start(env, {}) {
        let bus = new EventBus()
        registry.category("systray").add('activeCallsTray', {Component: ActiveCallsTray, props: {bus}})
        registry.category("main_components").add('activeCallsPopup', {Component: ActiveCallsPopup, props: {bus}})
    }
}
registry.category('services').add("active_calls", ActiveCallsService)

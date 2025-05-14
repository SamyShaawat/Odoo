/** @odoo-module **/
import {useService} from "@web/core/utils/hooks"

const {Component, useState} = owl

export class ActiveCallsPopup extends Component {
    static template = 'asterisk_plus.active_calls_popup'

    constructor(parent, props) {
        // console.log(parent, props)
        super(...arguments)
        this.state = useState({
            isDisplay: false,
            calls: [],
        })
        this.hideTimer = null
    }

    setup() {
        super.setup()
        this.rpc = useService('rpc')
        this.orm = useService('orm')
        const self = this
        this.props.bus.addEventListener('active_calls_toggle_display', (ev) => {
            self.toggleDisplay().then()
        })
    }

    async getCalls() {
        this.state.calls = await this.orm.call("asterisk_plus.call", "search_read", [
            [["is_active", "=", true]],
            ["calling_number", "called_number", "calling_user",
             "answered_user", "direction", "partner"]
        ])
        if (this.state.calls.length > 0) {
            this.setTimer(3000)
        } else {
            this.setTimer(600)
        }
    }

    setTimer(seconds) {
        const self = this
        self.hideTimer = setTimeout(() => {
            this.state.isDisplay = false
        }, seconds)
    }

    async toggleDisplay() {
        this.state.isDisplay = !this.state.isDisplay
        if (this.state.isDisplay) {
            await this.getCalls()
        } else {
            clearTimeout(this.hideTimer)
        }
    }

}


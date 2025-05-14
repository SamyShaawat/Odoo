/** @odoo-module **/

import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";

import { Component, useChildSubEnv, useState } from "@odoo/owl";
import { debounce } from "@web/core/utils/timing";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";

class BranchSelector {
    constructor(BranchService, toggleDelay) {
        this.BranchService = BranchService;
        this.selectedBranchesIds = BranchService.activeBranchIds.slice();
        this._debouncedApply = debounce(() => this._apply(), toggleDelay);
    }

    isBranchSelected(BranchId) {
        return this.selectedBranchesIds.includes(BranchId);
    }

    switchBranch(mode, BranchId) {
        if (mode === "toggle") {
            if (this.selectedBranchesIds.includes(BranchId)) {
                this._deselectBranch(BranchId);
            } else {
                this._selectBranch(BranchId);
            }
            this._debouncedApply();
        } else if (mode === "loginto") {
            this.selectedBranchesIds.splice(0, this.selectedBranchesIds.length);
            this._selectBranch(BranchId);
            this._apply();
        }
    }

    _selectBranch(BranchId) {
        if (!this.selectedBranchesIds.includes(BranchId)) {
            this.selectedBranchesIds.push(BranchId);
        }
    }

    _deselectBranch(BranchId) {
        if (this.selectedBranchesIds.includes(BranchId)) {
            this.selectedBranchesIds.splice(this.selectedBranchesIds.indexOf(BranchId), 1);
        }
    }

    _apply() {
        this.BranchService.setBranches(this.selectedBranchesIds);
    }
}

export class SwitchBranchItem extends Component {
    static template = "web.SwitchBranchItem";
    static components = { DropdownItem, SwitchBranchItem };
    static props = {
        branch: {},
        level: { type: Number },
    };

    setup() {
        this.BranchService = useService("Branch");
        this.BranchSelector = useState(this.env.BranchSelector);
    }
    
    get isBranchSelected() {
        return this.BranchSelector.isBranchSelected(this.props.branch.id);
    }
    get isBranchAllowed() {
        return this.props.branch.id in this.BranchService.allowedBranches;
    }
    get isCurrent() {
        return this.props.branch.id === this.BranchService.currentBranch.id;
    }

    logIntoBranch() {
        if (this.isBranchAllowed) {
            this.BranchSelector.switchBranch("loginto", this.props.branch.id);
        }
    }

    toggleBranch() {
        if (this.isBranchAllowed) {
            this.BranchSelector.switchBranch("toggle", this.props.branch.id);
        }
    }
}

export class SwitchBranchMenu extends Component {
    static template = "web.SwitchBranchMenu";
    static components = { Dropdown, DropdownItem, SwitchBranchItem };
    static props = {};
    static toggleDelay = 1000;

    setup() {
        this.BranchService = useService("Branch");
        this.BranchSelector = useState(
            new BranchSelector(this.BranchService, this.constructor.toggleDelay)
        );
        useChildSubEnv({ BranchSelector: this.BranchSelector });
    }
}

export const systrayItem = {
    Component: SwitchBranchMenu,
    isDisplayed(env) {
        const { allowedBranches } = env.services.Branch;
        return Object.keys(allowedBranches).length > 1;
    },
};
if (session.display_switch_branch_menu) {
    registry.category("systray").add("SwitchBranchMenu", systrayItem, { sequence: 1 });
}

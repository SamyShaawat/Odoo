/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { UPDATE_METHODS } from "@web/core/orm_service";
import { cookie } from "@web/core/browser/cookie";
import { jsonrpc } from "@web/core/network/rpc_service";

const BIDS_HASH_SEPARATOR = "-";

function parseBranchIds(bids, separator = ",") {
    if (typeof bids === "string") {
        return bids.split(separator).map(Number);
    } else if (typeof bids === "number") {
        return [bids];
    }
    return [];
}

function formatBranchIds(bids, separator = ",") {
    return bids.join(separator);
}

function computeActiveBranchIds(bids) {
    const { user_branches } = session;
    let activeBranchIds = bids || [];
    const availableBranchesFromSession = user_branches.allowed_branches;
    const notAllowedBranches = activeBranchIds.filter(
        (id) => !(id in availableBranchesFromSession)
    );

    if (!activeBranchIds.length || notAllowedBranches.length) {
        activeBranchIds = [user_branches.current_branch];
    }
    return activeBranchIds;
}

function getBranchIdsFromBrowser(hash) {
    let bids;
    if ("bids" in hash) {
        // backward compatibility s.t. old urls (still using "," as separator) keep working
        // deprecated as of 17.0
        let separator = BIDS_HASH_SEPARATOR;
        if (typeof hash.bids === "string" && !hash.bids.includes(BIDS_HASH_SEPARATOR)) {
            separator = ",";
        }
        bids = parseBranchIds(hash.bids, separator);
    } else if (cookie.get("bids")) {
        bids = parseBranchIds(cookie.get("bids"));
    }
    return bids || [];
}

const errorHandlerRegistry = registry.category("error_handlers");
function accessErrorHandler(env, error, originalError) {
    const router = env.services.router;
    const hash = router.current.hash;
    if (!hash._Branch_switching) {
        return false;
    }
    if (originalError?.exceptionName === "odoo.exceptions.AccessError") {
        const { model, id, view_type } = hash;
        if (!model || !id || view_type !== "form") {
            return false;
        }
        router.pushState({ view_type: undefined });

        browser.setTimeout(() => {
            // Force the WebClient to reload the state contained in the hash.
            env.bus.trigger("ROUTE_CHANGE");
        });
        if (error.event) {
            error.event.preventDefault();
        }
        return true;
    }
    return false;
}

export const BranchService = {
    dependencies: ["user", "router", "action"],
    start(env, { user, router, action }) {
        // Push an error handler in the registry. It needs to be before "rpcErrorHandler", which
        // has a sequence of 97. The default sequence of registry is 50.
        errorHandlerRegistry.add("accessErrorHandlerBranches", accessErrorHandler);

        const allowedBranches = session.user_branches.allowed_branches;
        const allowedBranchesWithAncestors = {
            ...allowedBranches,
        };
        const activeBranchIds = computeActiveBranchIds(
            getBranchIdsFromBrowser(router.current.hash)
        );

        // update browser data
        const bidsHash = formatBranchIds(activeBranchIds, BIDS_HASH_SEPARATOR);
        router.replaceState({ bids: bidsHash }, { lock: true });
        cookie.set("bids", formatBranchIds(activeBranchIds));
        user.updateContext({ allowed_branch_ids: activeBranchIds });

        // reload the page if changes are being done to `res.branch`
        env.bus.addEventListener("RPC:RESPONSE", (ev) => {
            const { data, error } = ev.detail;
            const { model, method } = data.params;
            if (!error && model === "res.branch" && UPDATE_METHODS.includes(method)) {
                if (!browser.localStorage.getItem("running_tour")) {
                    action.doAction("reload_context");
                }
            }
        });

        return {
            allowedBranches,
            allowedBranchesWithAncestors,

            get activeBranchIds() {
                return activeBranchIds.slice() || [1];
            },

            get currentBranch() {
                return allowedBranches[activeBranchIds[0]];
            },

            getBranch(BranchId) {
                return allowedBranchesWithAncestors[BranchId];
            },

            /**
             * @param {Array<>} BranchIds - List of branches to log into
             */
            setBranches(BranchIds) {
                const newBranchIds = BranchIds.length ? BranchIds : [activeBranchIds[0]];
                function addBranches(BranchIds) {
                    for (const BranchId of BranchIds) {
                        if (!newBranchIds.includes(BranchId)) {
                            newBranchIds.push(BranchId);
                        }
                    }
                }
                const bidsHash = formatBranchIds(newBranchIds, BIDS_HASH_SEPARATOR);
                router.pushState({ bids: bidsHash }, { lock: true });
                router.pushState({ _Branch_switching: true });
                cookie.set("bids", formatBranchIds(newBranchIds));
                jsonrpc('/set_brnach',{
                    BranchID: newBranchIds[0],
                })
                browser.setTimeout(() => browser.location.reload()); // history.pushState is a little async
            },
        };
    },
};
if (session.display_switch_branch_menu) {
    registry.category("services").add("Branch", BranchService);
}

import { DataBoard, Document, Picture, Setting, User, } from "@element-plus/icons-vue";
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { adminNavigation, adminNavigationGroups } from "../constants/navigation";
const route = useRoute();
const router = useRouter();
const iconMap = {
    DataBoard,
    Document,
    Picture,
    Setting,
    User,
};
const activePath = computed(() => (route.path === "/" ? "/" : route.path));
function handleSelect(index) {
    void router.push(index);
}
const __VLS_ctx = {
    ...{},
    ...{},
};
let __VLS_components;
let __VLS_intrinsics;
let __VLS_directives;
__VLS_asFunctionalElement1(__VLS_intrinsics.aside, __VLS_intrinsics.aside)({
    ...{ class: "app-sidebar" },
});
/** @type {__VLS_StyleScopedClasses['app-sidebar']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "sidebar-brand" },
});
/** @type {__VLS_StyleScopedClasses['sidebar-brand']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
    ...{ class: "sidebar-logo" },
    'aria-hidden': "true",
});
/** @type {__VLS_StyleScopedClasses['sidebar-logo']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "sidebar-mark" },
});
/** @type {__VLS_StyleScopedClasses['sidebar-mark']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.h1, __VLS_intrinsics.h1)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.nav, __VLS_intrinsics.nav)({
    ...{ class: "sidebar-nav" },
    'aria-label': "后台目录",
});
/** @type {__VLS_StyleScopedClasses['sidebar-nav']} */ ;
for (const [group] of __VLS_vFor((__VLS_ctx.adminNavigationGroups))) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
        key: (group.key),
        ...{ class: "sidebar-group" },
    });
    /** @type {__VLS_StyleScopedClasses['sidebar-group']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
        ...{ class: "sidebar-group-label" },
    });
    /** @type {__VLS_StyleScopedClasses['sidebar-group-label']} */ ;
    (group.label);
    let __VLS_0;
    /** @ts-ignore @type { | typeof __VLS_components.elMenu | typeof __VLS_components.ElMenu | typeof __VLS_components['el-menu'] | typeof __VLS_components.elMenu | typeof __VLS_components.ElMenu | typeof __VLS_components['el-menu']} */
    elMenu;
    // @ts-ignore
    const __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0({
        ...{ 'onSelect': {} },
        defaultActive: (__VLS_ctx.activePath),
        ...{ class: "sidebar-menu" },
        backgroundColor: "transparent",
        textColor: "#9aabba",
        activeTextColor: "#f5c66f",
    }));
    const __VLS_2 = __VLS_1({
        ...{ 'onSelect': {} },
        defaultActive: (__VLS_ctx.activePath),
        ...{ class: "sidebar-menu" },
        backgroundColor: "transparent",
        textColor: "#9aabba",
        activeTextColor: "#f5c66f",
    }, ...__VLS_functionalComponentArgsRest(__VLS_1));
    let __VLS_5;
    const __VLS_6 = {
        /** @type {typeof __VLS_5.select} */
        onSelect: (__VLS_ctx.handleSelect),
    };
    /** @type {__VLS_StyleScopedClasses['sidebar-menu']} */ ;
    const { default: __VLS_7 } = __VLS_3.slots;
    for (const [item] of __VLS_vFor((__VLS_ctx.adminNavigation.filter((entry) => entry.group === group.key)))) {
        let __VLS_8;
        /** @ts-ignore @type { | typeof __VLS_components.elMenuItem | typeof __VLS_components.ElMenuItem | typeof __VLS_components['el-menu-item'] | typeof __VLS_components.elMenuItem | typeof __VLS_components.ElMenuItem | typeof __VLS_components['el-menu-item']} */
        elMenuItem;
        // @ts-ignore
        const __VLS_9 = __VLS_asFunctionalComponent1(__VLS_8, new __VLS_8({
            key: (item.to),
            index: (item.to),
        }));
        const __VLS_10 = __VLS_9({
            key: (item.to),
            index: (item.to),
        }, ...__VLS_functionalComponentArgsRest(__VLS_9));
        const { default: __VLS_13 } = __VLS_11.slots;
        let __VLS_14;
        /** @ts-ignore @type { | typeof __VLS_components.elIcon | typeof __VLS_components.ElIcon | typeof __VLS_components['el-icon'] | typeof __VLS_components.elIcon | typeof __VLS_components.ElIcon | typeof __VLS_components['el-icon']} */
        elIcon;
        // @ts-ignore
        const __VLS_15 = __VLS_asFunctionalComponent1(__VLS_14, new __VLS_14({}));
        const __VLS_16 = __VLS_15({}, ...__VLS_functionalComponentArgsRest(__VLS_15));
        const { default: __VLS_19 } = __VLS_17.slots;
        const __VLS_20 = (__VLS_ctx.iconMap[item.icon]);
        // @ts-ignore
        const __VLS_21 = __VLS_asFunctionalComponent1(__VLS_20, new __VLS_20({}));
        const __VLS_22 = __VLS_21({}, ...__VLS_functionalComponentArgsRest(__VLS_21));
        // @ts-ignore
        [adminNavigationGroups, activePath, handleSelect, adminNavigation, iconMap,];
        var __VLS_17;
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
        (item.label);
        // @ts-ignore
        [];
        var __VLS_11;
        // @ts-ignore
        [];
    }
    // @ts-ignore
    [];
    var __VLS_3;
    var __VLS_4;
    // @ts-ignore
    [];
}
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "sidebar-footer" },
});
/** @type {__VLS_StyleScopedClasses['sidebar-footer']} */ ;
// @ts-ignore
[];
const __VLS_export = (await import('vue')).defineComponent({});
export default {};

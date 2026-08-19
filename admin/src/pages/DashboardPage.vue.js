import { Calendar, DataLine, EditPen, MagicStick } from "@element-plus/icons-vue";
import PageHeader from "../components/PageHeader.vue";
const summaryCards = [
    { title: "首页视觉", value: "01", description: "当前已接入欢迎页配置和名句轮播", icon: MagicStick },
    { title: "文章模块", value: "04", description: "已预留列表、编辑、标签、分类扩展位", icon: EditPen },
    { title: "内容计划", value: "03", description: "媒体、关于自己、系统设置待继续落地", icon: DataLine },
    { title: "上线节奏", value: "本周", description: "建议优先补文章管理和图片上传", icon: Calendar },
];
const todoList = [
    "接入文章列表与文章编辑页",
    "把首页封面图 URL 升级成图片上传",
    "补齐关于自己模块的数据表单",
    "增加系统设置与操作日志入口",
];
const __VLS_ctx = {
    ...{},
    ...{},
};
let __VLS_components;
let __VLS_intrinsics;
let __VLS_directives;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "page-stack" },
});
/** @type {__VLS_StyleScopedClasses['page-stack']} */ ;
const __VLS_0 = PageHeader;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0({
    eyebrow: "DASHBOARD",
    title: "控制台",
    description: "这是后台的总览工作台，用来快速查看当前模块准备情况和下一步开发重点。",
}));
const __VLS_2 = __VLS_1({
    eyebrow: "DASHBOARD",
    title: "控制台",
    description: "这是后台的总览工作台，用来快速查看当前模块准备情况和下一步开发重点。",
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
let __VLS_5;
/** @ts-ignore @type { | typeof __VLS_components.elRow | typeof __VLS_components.ElRow | typeof __VLS_components['el-row'] | typeof __VLS_components.elRow | typeof __VLS_components.ElRow | typeof __VLS_components['el-row']} */
elRow;
// @ts-ignore
const __VLS_6 = __VLS_asFunctionalComponent1(__VLS_5, new __VLS_5({
    gutter: (16),
}));
const __VLS_7 = __VLS_6({
    gutter: (16),
}, ...__VLS_functionalComponentArgsRest(__VLS_6));
const { default: __VLS_10 } = __VLS_8.slots;
for (const [card] of __VLS_vFor((__VLS_ctx.summaryCards))) {
    let __VLS_11;
    /** @ts-ignore @type { | typeof __VLS_components.elCol | typeof __VLS_components.ElCol | typeof __VLS_components['el-col'] | typeof __VLS_components.elCol | typeof __VLS_components.ElCol | typeof __VLS_components['el-col']} */
    elCol;
    // @ts-ignore
    const __VLS_12 = __VLS_asFunctionalComponent1(__VLS_11, new __VLS_11({
        key: (card.title),
        xs: (24),
        sm: (12),
        xl: (6),
    }));
    const __VLS_13 = __VLS_12({
        key: (card.title),
        xs: (24),
        sm: (12),
        xl: (6),
    }, ...__VLS_functionalComponentArgsRest(__VLS_12));
    const { default: __VLS_16 } = __VLS_14.slots;
    let __VLS_17;
    /** @ts-ignore @type { | typeof __VLS_components.elCard | typeof __VLS_components.ElCard | typeof __VLS_components['el-card'] | typeof __VLS_components.elCard | typeof __VLS_components.ElCard | typeof __VLS_components['el-card']} */
    elCard;
    // @ts-ignore
    const __VLS_18 = __VLS_asFunctionalComponent1(__VLS_17, new __VLS_17({
        shadow: "hover",
        ...{ class: "dashboard-stat-card" },
    }));
    const __VLS_19 = __VLS_18({
        shadow: "hover",
        ...{ class: "dashboard-stat-card" },
    }, ...__VLS_functionalComponentArgsRest(__VLS_18));
    /** @type {__VLS_StyleScopedClasses['dashboard-stat-card']} */ ;
    const { default: __VLS_22 } = __VLS_20.slots;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "dashboard-stat-top" },
    });
    /** @type {__VLS_StyleScopedClasses['dashboard-stat-top']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
    __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
        ...{ class: "dashboard-stat-title" },
    });
    /** @type {__VLS_StyleScopedClasses['dashboard-stat-title']} */ ;
    (card.title);
    __VLS_asFunctionalElement1(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
    (card.value);
    let __VLS_23;
    /** @ts-ignore @type { | typeof __VLS_components.elIcon | typeof __VLS_components.ElIcon | typeof __VLS_components['el-icon'] | typeof __VLS_components.elIcon | typeof __VLS_components.ElIcon | typeof __VLS_components['el-icon']} */
    elIcon;
    // @ts-ignore
    const __VLS_24 = __VLS_asFunctionalComponent1(__VLS_23, new __VLS_23({
        ...{ class: "dashboard-stat-icon" },
    }));
    const __VLS_25 = __VLS_24({
        ...{ class: "dashboard-stat-icon" },
    }, ...__VLS_functionalComponentArgsRest(__VLS_24));
    /** @type {__VLS_StyleScopedClasses['dashboard-stat-icon']} */ ;
    const { default: __VLS_28 } = __VLS_26.slots;
    const __VLS_29 = (card.icon);
    // @ts-ignore
    const __VLS_30 = __VLS_asFunctionalComponent1(__VLS_29, new __VLS_29({}));
    const __VLS_31 = __VLS_30({}, ...__VLS_functionalComponentArgsRest(__VLS_30));
    // @ts-ignore
    [summaryCards,];
    var __VLS_26;
    __VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
        ...{ class: "dashboard-stat-text" },
    });
    /** @type {__VLS_StyleScopedClasses['dashboard-stat-text']} */ ;
    (card.description);
    // @ts-ignore
    [];
    var __VLS_20;
    // @ts-ignore
    [];
    var __VLS_14;
    // @ts-ignore
    [];
}
// @ts-ignore
[];
var __VLS_8;
let __VLS_34;
/** @ts-ignore @type { | typeof __VLS_components.elRow | typeof __VLS_components.ElRow | typeof __VLS_components['el-row'] | typeof __VLS_components.elRow | typeof __VLS_components.ElRow | typeof __VLS_components['el-row']} */
elRow;
// @ts-ignore
const __VLS_35 = __VLS_asFunctionalComponent1(__VLS_34, new __VLS_34({
    gutter: (16),
}));
const __VLS_36 = __VLS_35({
    gutter: (16),
}, ...__VLS_functionalComponentArgsRest(__VLS_35));
const { default: __VLS_39 } = __VLS_37.slots;
let __VLS_40;
/** @ts-ignore @type { | typeof __VLS_components.elCol | typeof __VLS_components.ElCol | typeof __VLS_components['el-col'] | typeof __VLS_components.elCol | typeof __VLS_components.ElCol | typeof __VLS_components['el-col']} */
elCol;
// @ts-ignore
const __VLS_41 = __VLS_asFunctionalComponent1(__VLS_40, new __VLS_40({
    xs: (24),
    xl: (16),
}));
const __VLS_42 = __VLS_41({
    xs: (24),
    xl: (16),
}, ...__VLS_functionalComponentArgsRest(__VLS_41));
const { default: __VLS_45 } = __VLS_43.slots;
let __VLS_46;
/** @ts-ignore @type { | typeof __VLS_components.elCard | typeof __VLS_components.ElCard | typeof __VLS_components['el-card'] | typeof __VLS_components.elCard | typeof __VLS_components.ElCard | typeof __VLS_components['el-card']} */
elCard;
// @ts-ignore
const __VLS_47 = __VLS_asFunctionalComponent1(__VLS_46, new __VLS_46({
    shadow: "never",
    ...{ class: "dashboard-panel" },
}));
const __VLS_48 = __VLS_47({
    shadow: "never",
    ...{ class: "dashboard-panel" },
}, ...__VLS_functionalComponentArgsRest(__VLS_47));
/** @type {__VLS_StyleScopedClasses['dashboard-panel']} */ ;
const { default: __VLS_51 } = __VLS_49.slots;
{
    const { header: __VLS_52 } = __VLS_49.slots;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "panel-header" },
    });
    /** @type {__VLS_StyleScopedClasses['panel-header']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    let __VLS_53;
    /** @ts-ignore @type { | typeof __VLS_components.elTag | typeof __VLS_components.ElTag | typeof __VLS_components['el-tag'] | typeof __VLS_components.elTag | typeof __VLS_components.ElTag | typeof __VLS_components['el-tag']} */
    elTag;
    // @ts-ignore
    const __VLS_54 = __VLS_asFunctionalComponent1(__VLS_53, new __VLS_53({
        type: "warning",
    }));
    const __VLS_55 = __VLS_54({
        type: "warning",
    }, ...__VLS_functionalComponentArgsRest(__VLS_54));
    const { default: __VLS_58 } = __VLS_56.slots;
    // @ts-ignore
    [];
    var __VLS_56;
    // @ts-ignore
    [];
}
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "dashboard-module-grid" },
});
/** @type {__VLS_StyleScopedClasses['dashboard-module-grid']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "dashboard-module-item" },
});
/** @type {__VLS_StyleScopedClasses['dashboard-module-item']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.h3, __VLS_intrinsics.h3)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "dashboard-module-item" },
});
/** @type {__VLS_StyleScopedClasses['dashboard-module-item']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.h3, __VLS_intrinsics.h3)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "dashboard-module-item" },
});
/** @type {__VLS_StyleScopedClasses['dashboard-module-item']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.h3, __VLS_intrinsics.h3)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "dashboard-module-item" },
});
/** @type {__VLS_StyleScopedClasses['dashboard-module-item']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.h3, __VLS_intrinsics.h3)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
// @ts-ignore
[];
var __VLS_49;
// @ts-ignore
[];
var __VLS_43;
let __VLS_59;
/** @ts-ignore @type { | typeof __VLS_components.elCol | typeof __VLS_components.ElCol | typeof __VLS_components['el-col'] | typeof __VLS_components.elCol | typeof __VLS_components.ElCol | typeof __VLS_components['el-col']} */
elCol;
// @ts-ignore
const __VLS_60 = __VLS_asFunctionalComponent1(__VLS_59, new __VLS_59({
    xs: (24),
    xl: (8),
}));
const __VLS_61 = __VLS_60({
    xs: (24),
    xl: (8),
}, ...__VLS_functionalComponentArgsRest(__VLS_60));
const { default: __VLS_64 } = __VLS_62.slots;
let __VLS_65;
/** @ts-ignore @type { | typeof __VLS_components.elCard | typeof __VLS_components.ElCard | typeof __VLS_components['el-card'] | typeof __VLS_components.elCard | typeof __VLS_components.ElCard | typeof __VLS_components['el-card']} */
elCard;
// @ts-ignore
const __VLS_66 = __VLS_asFunctionalComponent1(__VLS_65, new __VLS_65({
    shadow: "never",
    ...{ class: "dashboard-panel" },
}));
const __VLS_67 = __VLS_66({
    shadow: "never",
    ...{ class: "dashboard-panel" },
}, ...__VLS_functionalComponentArgsRest(__VLS_66));
/** @type {__VLS_StyleScopedClasses['dashboard-panel']} */ ;
const { default: __VLS_70 } = __VLS_68.slots;
{
    const { header: __VLS_71 } = __VLS_68.slots;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "panel-header" },
    });
    /** @type {__VLS_StyleScopedClasses['panel-header']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    // @ts-ignore
    [];
}
let __VLS_72;
/** @ts-ignore @type { | typeof __VLS_components.elTimeline | typeof __VLS_components.ElTimeline | typeof __VLS_components['el-timeline'] | typeof __VLS_components.elTimeline | typeof __VLS_components.ElTimeline | typeof __VLS_components['el-timeline']} */
elTimeline;
// @ts-ignore
const __VLS_73 = __VLS_asFunctionalComponent1(__VLS_72, new __VLS_72({}));
const __VLS_74 = __VLS_73({}, ...__VLS_functionalComponentArgsRest(__VLS_73));
const { default: __VLS_77 } = __VLS_75.slots;
for (const [item] of __VLS_vFor((__VLS_ctx.todoList))) {
    let __VLS_78;
    /** @ts-ignore @type { | typeof __VLS_components.elTimelineItem | typeof __VLS_components.ElTimelineItem | typeof __VLS_components['el-timeline-item'] | typeof __VLS_components.elTimelineItem | typeof __VLS_components.ElTimelineItem | typeof __VLS_components['el-timeline-item']} */
    elTimelineItem;
    // @ts-ignore
    const __VLS_79 = __VLS_asFunctionalComponent1(__VLS_78, new __VLS_78({
        key: (item),
        type: "warning",
        hollow: true,
        timestamp: ('推荐优先级'),
    }));
    const __VLS_80 = __VLS_79({
        key: (item),
        type: "warning",
        hollow: true,
        timestamp: ('推荐优先级'),
    }, ...__VLS_functionalComponentArgsRest(__VLS_79));
    const { default: __VLS_83 } = __VLS_81.slots;
    (item);
    // @ts-ignore
    [todoList,];
    var __VLS_81;
    // @ts-ignore
    [];
}
// @ts-ignore
[];
var __VLS_75;
// @ts-ignore
[];
var __VLS_68;
// @ts-ignore
[];
var __VLS_62;
// @ts-ignore
[];
var __VLS_37;
// @ts-ignore
[];
const __VLS_export = (await import('vue')).defineComponent({});
export default {};

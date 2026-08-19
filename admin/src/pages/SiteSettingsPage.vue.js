import { Check, Link } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { computed, onMounted, ref } from "vue";
import { fetchSiteSettings, updateSiteSettings } from "../api/site-settings";
import PageHeader from "../components/PageHeader.vue";
const form = ref({
    site_subtitle: "自由、梦想、伙伴，这里记录我向前航行的每一步。",
    hero_image_url: "https://images.hdqwalls.com/download/one-piece-anime-artwork-i6-2560x1440.jpg",
    nav_brand: "某某某的个人空间",
    quotes: [],
});
const statusText = ref("正在读取首页配置...");
const saving = ref(false);
const quoteDraft = ref("");
const previewQuotes = computed(() => quoteDraft.value.split("\n").filter(Boolean).slice(0, 3));
function formatQuotes(quotes) {
    quoteDraft.value = quotes
        .map((item) => `${item.author}|${item.text}`)
        .join("\n");
}
function parseQuotes() {
    return quoteDraft.value
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => {
        const [author, text] = line.split("|").map((item) => item.trim());
        return { author, text };
    });
}
async function loadSettings() {
    try {
        const payload = await fetchSiteSettings();
        form.value = payload;
        formatQuotes(payload.quotes);
        statusText.value = "首页配置已加载，可直接修改。";
    }
    catch {
        statusText.value = "读取失败，请确认后端服务已启动。";
    }
}
async function saveSettings() {
    saving.value = true;
    statusText.value = "正在保存首页配置...";
    try {
        const payload = {
            ...form.value,
            quotes: parseQuotes(),
        };
        const nextValue = await updateSiteSettings(payload);
        form.value = nextValue;
        formatQuotes(nextValue.quotes);
        statusText.value = "保存成功，前台刷新后即可看到新的封面图和语录。";
        ElMessage.success("首页配置已保存");
    }
    catch {
        statusText.value = "保存失败，请检查语录格式是否为：角色|台词";
        ElMessage.error("保存失败，请检查语录格式");
    }
    finally {
        saving.value = false;
    }
}
onMounted(() => {
    void loadSettings();
});
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
    eyebrow: "SITE SETTINGS",
    title: "首页欢迎页配置",
    description: "这里管理首屏大图、副标题、导航品牌和经典语句轮播。",
}));
const __VLS_2 = __VLS_1({
    eyebrow: "SITE SETTINGS",
    title: "首页欢迎页配置",
    description: "这里管理首屏大图、副标题、导航品牌和经典语句轮播。",
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "status-panel" },
});
/** @type {__VLS_StyleScopedClasses['status-panel']} */ ;
let __VLS_5;
/** @ts-ignore @type { | typeof __VLS_components.elIcon | typeof __VLS_components.ElIcon | typeof __VLS_components['el-icon'] | typeof __VLS_components.elIcon | typeof __VLS_components.ElIcon | typeof __VLS_components['el-icon']} */
elIcon;
// @ts-ignore
const __VLS_6 = __VLS_asFunctionalComponent1(__VLS_5, new __VLS_5({}));
const __VLS_7 = __VLS_6({}, ...__VLS_functionalComponentArgsRest(__VLS_6));
const { default: __VLS_10 } = __VLS_8.slots;
let __VLS_11;
/** @ts-ignore @type { | typeof __VLS_components.Check} */
Check;
// @ts-ignore
const __VLS_12 = __VLS_asFunctionalComponent1(__VLS_11, new __VLS_11({}));
const __VLS_13 = __VLS_12({}, ...__VLS_functionalComponentArgsRest(__VLS_12));
var __VLS_8;
(__VLS_ctx.statusText);
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "settings-grid" },
});
/** @type {__VLS_StyleScopedClasses['settings-grid']} */ ;
let __VLS_16;
/** @ts-ignore @type { | typeof __VLS_components.elCard | typeof __VLS_components.ElCard | typeof __VLS_components['el-card'] | typeof __VLS_components.elCard | typeof __VLS_components.ElCard | typeof __VLS_components['el-card']} */
elCard;
// @ts-ignore
const __VLS_17 = __VLS_asFunctionalComponent1(__VLS_16, new __VLS_16({
    shadow: "never",
    ...{ class: "form-card" },
}));
const __VLS_18 = __VLS_17({
    shadow: "never",
    ...{ class: "form-card" },
}, ...__VLS_functionalComponentArgsRest(__VLS_17));
/** @type {__VLS_StyleScopedClasses['form-card']} */ ;
const { default: __VLS_21 } = __VLS_19.slots;
{
    const { header: __VLS_22 } = __VLS_19.slots;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "panel-header" },
    });
    /** @type {__VLS_StyleScopedClasses['panel-header']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    let __VLS_23;
    /** @ts-ignore @type { | typeof __VLS_components.elTag | typeof __VLS_components.ElTag | typeof __VLS_components['el-tag'] | typeof __VLS_components.elTag | typeof __VLS_components.ElTag | typeof __VLS_components['el-tag']} */
    elTag;
    // @ts-ignore
    const __VLS_24 = __VLS_asFunctionalComponent1(__VLS_23, new __VLS_23({
        type: "warning",
    }));
    const __VLS_25 = __VLS_24({
        type: "warning",
    }, ...__VLS_functionalComponentArgsRest(__VLS_24));
    const { default: __VLS_28 } = __VLS_26.slots;
    // @ts-ignore
    [statusText,];
    var __VLS_26;
    // @ts-ignore
    [];
}
let __VLS_29;
/** @ts-ignore @type { | typeof __VLS_components.elForm | typeof __VLS_components.ElForm | typeof __VLS_components['el-form'] | typeof __VLS_components.elForm | typeof __VLS_components.ElForm | typeof __VLS_components['el-form']} */
elForm;
// @ts-ignore
const __VLS_30 = __VLS_asFunctionalComponent1(__VLS_29, new __VLS_29({
    ...{ 'onSubmit': {} },
    labelPosition: "top",
    ...{ class: "settings-form" },
}));
const __VLS_31 = __VLS_30({
    ...{ 'onSubmit': {} },
    labelPosition: "top",
    ...{ class: "settings-form" },
}, ...__VLS_functionalComponentArgsRest(__VLS_30));
let __VLS_34;
const __VLS_35 = {
    /** @type {typeof __VLS_34.submit} */
    onSubmit: (__VLS_ctx.saveSettings),
};
/** @type {__VLS_StyleScopedClasses['settings-form']} */ ;
const { default: __VLS_36 } = __VLS_32.slots;
let __VLS_37;
/** @ts-ignore @type { | typeof __VLS_components.elFormItem | typeof __VLS_components.ElFormItem | typeof __VLS_components['el-form-item'] | typeof __VLS_components.elFormItem | typeof __VLS_components.ElFormItem | typeof __VLS_components['el-form-item']} */
elFormItem;
// @ts-ignore
const __VLS_38 = __VLS_asFunctionalComponent1(__VLS_37, new __VLS_37({
    label: "站点副标题",
}));
const __VLS_39 = __VLS_38({
    label: "站点副标题",
}, ...__VLS_functionalComponentArgsRest(__VLS_38));
const { default: __VLS_42 } = __VLS_40.slots;
let __VLS_43;
/** @ts-ignore @type { | typeof __VLS_components.elInput | typeof __VLS_components.ElInput | typeof __VLS_components['el-input']} */
elInput;
// @ts-ignore
const __VLS_44 = __VLS_asFunctionalComponent1(__VLS_43, new __VLS_43({
    modelValue: (__VLS_ctx.form.site_subtitle),
    placeholder: "自由、梦想、伙伴，这里记录我向前航行的每一步。",
}));
const __VLS_45 = __VLS_44({
    modelValue: (__VLS_ctx.form.site_subtitle),
    placeholder: "自由、梦想、伙伴，这里记录我向前航行的每一步。",
}, ...__VLS_functionalComponentArgsRest(__VLS_44));
// @ts-ignore
[saveSettings, form,];
var __VLS_40;
let __VLS_48;
/** @ts-ignore @type { | typeof __VLS_components.elFormItem | typeof __VLS_components.ElFormItem | typeof __VLS_components['el-form-item'] | typeof __VLS_components.elFormItem | typeof __VLS_components.ElFormItem | typeof __VLS_components['el-form-item']} */
elFormItem;
// @ts-ignore
const __VLS_49 = __VLS_asFunctionalComponent1(__VLS_48, new __VLS_48({
    label: "导航品牌名",
}));
const __VLS_50 = __VLS_49({
    label: "导航品牌名",
}, ...__VLS_functionalComponentArgsRest(__VLS_49));
const { default: __VLS_53 } = __VLS_51.slots;
let __VLS_54;
/** @ts-ignore @type { | typeof __VLS_components.elInput | typeof __VLS_components.ElInput | typeof __VLS_components['el-input']} */
elInput;
// @ts-ignore
const __VLS_55 = __VLS_asFunctionalComponent1(__VLS_54, new __VLS_54({
    modelValue: (__VLS_ctx.form.nav_brand),
    placeholder: "某某某的个人空间",
}));
const __VLS_56 = __VLS_55({
    modelValue: (__VLS_ctx.form.nav_brand),
    placeholder: "某某某的个人空间",
}, ...__VLS_functionalComponentArgsRest(__VLS_55));
// @ts-ignore
[form,];
var __VLS_51;
let __VLS_59;
/** @ts-ignore @type { | typeof __VLS_components.elFormItem | typeof __VLS_components.ElFormItem | typeof __VLS_components['el-form-item'] | typeof __VLS_components.elFormItem | typeof __VLS_components.ElFormItem | typeof __VLS_components['el-form-item']} */
elFormItem;
// @ts-ignore
const __VLS_60 = __VLS_asFunctionalComponent1(__VLS_59, new __VLS_59({
    label: "封面图 URL",
}));
const __VLS_61 = __VLS_60({
    label: "封面图 URL",
}, ...__VLS_functionalComponentArgsRest(__VLS_60));
const { default: __VLS_64 } = __VLS_62.slots;
let __VLS_65;
/** @ts-ignore @type { | typeof __VLS_components.elInput | typeof __VLS_components.ElInput | typeof __VLS_components['el-input'] | typeof __VLS_components.elInput | typeof __VLS_components.ElInput | typeof __VLS_components['el-input']} */
elInput;
// @ts-ignore
const __VLS_66 = __VLS_asFunctionalComponent1(__VLS_65, new __VLS_65({
    modelValue: (__VLS_ctx.form.hero_image_url),
    type: "textarea",
    rows: (3),
    placeholder: "填写可访问的海贼王风格封面图地址",
}));
const __VLS_67 = __VLS_66({
    modelValue: (__VLS_ctx.form.hero_image_url),
    type: "textarea",
    rows: (3),
    placeholder: "填写可访问的海贼王风格封面图地址",
}, ...__VLS_functionalComponentArgsRest(__VLS_66));
const { default: __VLS_70 } = __VLS_68.slots;
{
    const { prefix: __VLS_71 } = __VLS_68.slots;
    let __VLS_72;
    /** @ts-ignore @type { | typeof __VLS_components.elIcon | typeof __VLS_components.ElIcon | typeof __VLS_components['el-icon'] | typeof __VLS_components.elIcon | typeof __VLS_components.ElIcon | typeof __VLS_components['el-icon']} */
    elIcon;
    // @ts-ignore
    const __VLS_73 = __VLS_asFunctionalComponent1(__VLS_72, new __VLS_72({}));
    const __VLS_74 = __VLS_73({}, ...__VLS_functionalComponentArgsRest(__VLS_73));
    const { default: __VLS_77 } = __VLS_75.slots;
    let __VLS_78;
    /** @ts-ignore @type { | typeof __VLS_components.Link} */
    Link;
    // @ts-ignore
    const __VLS_79 = __VLS_asFunctionalComponent1(__VLS_78, new __VLS_78({}));
    const __VLS_80 = __VLS_79({}, ...__VLS_functionalComponentArgsRest(__VLS_79));
    // @ts-ignore
    [form,];
    var __VLS_75;
    // @ts-ignore
    [];
}
// @ts-ignore
[];
var __VLS_68;
// @ts-ignore
[];
var __VLS_62;
let __VLS_83;
/** @ts-ignore @type { | typeof __VLS_components.elFormItem | typeof __VLS_components.ElFormItem | typeof __VLS_components['el-form-item'] | typeof __VLS_components.elFormItem | typeof __VLS_components.ElFormItem | typeof __VLS_components['el-form-item']} */
elFormItem;
// @ts-ignore
const __VLS_84 = __VLS_asFunctionalComponent1(__VLS_83, new __VLS_83({
    label: "经典语句",
}));
const __VLS_85 = __VLS_84({
    label: "经典语句",
}, ...__VLS_functionalComponentArgsRest(__VLS_84));
const { default: __VLS_88 } = __VLS_86.slots;
let __VLS_89;
/** @ts-ignore @type { | typeof __VLS_components.elInput | typeof __VLS_components.ElInput | typeof __VLS_components['el-input']} */
elInput;
// @ts-ignore
const __VLS_90 = __VLS_asFunctionalComponent1(__VLS_89, new __VLS_89({
    modelValue: (__VLS_ctx.quoteDraft),
    type: "textarea",
    rows: (8),
    placeholder: "每行一个：角色|台词",
}));
const __VLS_91 = __VLS_90({
    modelValue: (__VLS_ctx.quoteDraft),
    type: "textarea",
    rows: (8),
    placeholder: "每行一个：角色|台词",
}, ...__VLS_functionalComponentArgsRest(__VLS_90));
// @ts-ignore
[quoteDraft,];
var __VLS_86;
let __VLS_94;
/** @ts-ignore @type { | typeof __VLS_components.elButton | typeof __VLS_components.ElButton | typeof __VLS_components['el-button'] | typeof __VLS_components.elButton | typeof __VLS_components.ElButton | typeof __VLS_components['el-button']} */
elButton;
// @ts-ignore
const __VLS_95 = __VLS_asFunctionalComponent1(__VLS_94, new __VLS_94({
    ...{ 'onClick': {} },
    type: "primary",
    size: "large",
    loading: (__VLS_ctx.saving),
}));
const __VLS_96 = __VLS_95({
    ...{ 'onClick': {} },
    type: "primary",
    size: "large",
    loading: (__VLS_ctx.saving),
}, ...__VLS_functionalComponentArgsRest(__VLS_95));
let __VLS_99;
const __VLS_100 = {
    /** @type {typeof __VLS_99.click} */
    onClick: (__VLS_ctx.saveSettings),
};
const { default: __VLS_101 } = __VLS_97.slots;
// @ts-ignore
[saveSettings, saving,];
var __VLS_97;
var __VLS_98;
// @ts-ignore
[];
var __VLS_32;
var __VLS_33;
// @ts-ignore
[];
var __VLS_19;
let __VLS_102;
/** @ts-ignore @type { | typeof __VLS_components.elCard | typeof __VLS_components.ElCard | typeof __VLS_components['el-card'] | typeof __VLS_components.elCard | typeof __VLS_components.ElCard | typeof __VLS_components['el-card']} */
elCard;
// @ts-ignore
const __VLS_103 = __VLS_asFunctionalComponent1(__VLS_102, new __VLS_102({
    shadow: "never",
    ...{ class: "preview-card" },
}));
const __VLS_104 = __VLS_103({
    shadow: "never",
    ...{ class: "preview-card" },
}, ...__VLS_functionalComponentArgsRest(__VLS_103));
/** @type {__VLS_StyleScopedClasses['preview-card']} */ ;
const { default: __VLS_107 } = __VLS_105.slots;
{
    const { header: __VLS_108 } = __VLS_105.slots;
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "panel-header" },
    });
    /** @type {__VLS_StyleScopedClasses['panel-header']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    let __VLS_109;
    /** @ts-ignore @type { | typeof __VLS_components.elTag | typeof __VLS_components.ElTag | typeof __VLS_components['el-tag'] | typeof __VLS_components.elTag | typeof __VLS_components.ElTag | typeof __VLS_components['el-tag']} */
    elTag;
    // @ts-ignore
    const __VLS_110 = __VLS_asFunctionalComponent1(__VLS_109, new __VLS_109({
        effect: "plain",
    }));
    const __VLS_111 = __VLS_110({
        effect: "plain",
    }, ...__VLS_functionalComponentArgsRest(__VLS_110));
    const { default: __VLS_114 } = __VLS_112.slots;
    // @ts-ignore
    [];
    var __VLS_112;
    // @ts-ignore
    [];
}
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "preview-hero" },
    ...{ style: ({ backgroundImage: `url(${__VLS_ctx.form.hero_image_url})` }) },
});
/** @type {__VLS_StyleScopedClasses['preview-hero']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "preview-mask" },
});
/** @type {__VLS_StyleScopedClasses['preview-mask']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
(__VLS_ctx.form.site_subtitle);
__VLS_asFunctionalElement1(__VLS_intrinsics.ul, __VLS_intrinsics.ul)({});
for (const [line] of __VLS_vFor((__VLS_ctx.previewQuotes))) {
    __VLS_asFunctionalElement1(__VLS_intrinsics.li, __VLS_intrinsics.li)({
        key: (line),
    });
    (line);
    // @ts-ignore
    [form, form, previewQuotes,];
}
// @ts-ignore
[];
var __VLS_105;
// @ts-ignore
[];
const __VLS_export = (await import('vue')).defineComponent({});
export default {};

import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { fetchSiteSettings } from "./api/site-settings";
const fallbackSettings = {
    site_subtitle: "自由、梦想、伙伴，这里记录我向前航行的每一步。",
    hero_image_url: "https://images.hdqwalls.com/download/one-piece-anime-artwork-i6-2560x1440.jpg",
    nav_brand: "某某某的个人空间",
    quotes: [
        {
            author: "路飞",
            text: "我是要成为海贼王的男人。",
        },
        {
            author: "希鲁鲁克",
            text: "人被世人遗忘的时候，才是真正的死亡。",
        },
        {
            author: "罗宾",
            text: "我想活下去。",
        },
    ],
};
const settings = ref(fallbackSettings);
const navVisible = ref(true);
const navRevealing = ref(false);
const activeQuoteIndex = ref(0);
const typedCharacters = ref(0);
let quoteTimer;
let switchTimer;
let navRevealTimer;
let lastScrollY = 0;
const activeQuote = computed(() => settings.value.quotes[activeQuoteIndex.value] ?? fallbackSettings.quotes[0]);
const typedQuote = computed(() => activeQuote.value.text.slice(0, typedCharacters.value));
async function loadSettings() {
    try {
        settings.value = await fetchSiteSettings();
    }
    catch {
        settings.value = fallbackSettings;
    }
}
function startTypingCycle() {
    window.clearInterval(quoteTimer);
    window.clearTimeout(switchTimer);
    typedCharacters.value = 0;
    quoteTimer = window.setInterval(() => {
        if (typedCharacters.value >= activeQuote.value.text.length) {
            window.clearInterval(quoteTimer);
            switchTimer = window.setTimeout(() => {
                activeQuoteIndex.value = (activeQuoteIndex.value + 1) % settings.value.quotes.length;
                startTypingCycle();
            }, 2600);
            return;
        }
        typedCharacters.value += 1;
    }, 130);
}
function handleScroll() {
    const currentY = window.scrollY;
    const scrollingUp = currentY < lastScrollY;
    navVisible.value = currentY < 24 || scrollingUp;
    if (scrollingUp && currentY >= 24) {
        navRevealing.value = true;
        window.clearTimeout(navRevealTimer);
        navRevealTimer = window.setTimeout(() => {
            navRevealing.value = false;
        }, 1200);
    }
    else if (!scrollingUp) {
        navRevealing.value = false;
        window.clearTimeout(navRevealTimer);
    }
    lastScrollY = currentY;
}
onMounted(async () => {
    await loadSettings();
    startTypingCycle();
    window.addEventListener("scroll", handleScroll, { passive: true });
});
onBeforeUnmount(() => {
    window.removeEventListener("scroll", handleScroll);
    window.clearInterval(quoteTimer);
    window.clearTimeout(switchTimer);
    window.clearTimeout(navRevealTimer);
});
const __VLS_ctx = {
    ...{},
    ...{},
};
let __VLS_components;
let __VLS_intrinsics;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['floating-nav']} */ ;
/** @type {__VLS_StyleScopedClasses['floating-nav']} */ ;
/** @type {__VLS_StyleScopedClasses['floating-nav']} */ ;
/** @type {__VLS_StyleScopedClasses['floating-nav']} */ ;
/** @type {__VLS_StyleScopedClasses['brand']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-route']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-overlay']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-overlay']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-overlay']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-overlay']} */ ;
/** @type {__VLS_StyleScopedClasses['scroll-indicator']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-card']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-card']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-card']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-card']} */ ;
/** @type {__VLS_StyleScopedClasses['split-section']} */ ;
/** @type {__VLS_StyleScopedClasses['timeline-item']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['split-section']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['glass-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['timeline-item']} */ ;
/** @type {__VLS_StyleScopedClasses['timeline-item']} */ ;
/** @type {__VLS_StyleScopedClasses['floating-nav']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['split-section']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-route']} */ ;
/** @type {__VLS_StyleScopedClasses['floating-nav']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-atmosphere']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-route']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-route']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-overlay']} */ ;
/** @type {__VLS_StyleScopedClasses['scroll-arrow']} */ ;
/** @type {__VLS_StyleScopedClasses['timeline-item']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-overlay']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-card']} */ ;
/** @type {__VLS_StyleScopedClasses['scroll-indicator']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "page-shell" },
});
/** @type {__VLS_StyleScopedClasses['page-shell']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.header, __VLS_intrinsics.header)({
    ...{ class: (['floating-nav', { hidden: !__VLS_ctx.navVisible, revealing: __VLS_ctx.navRevealing }]) },
});
/** @type {__VLS_StyleScopedClasses['hidden']} */ ;
/** @type {__VLS_StyleScopedClasses['revealing']} */ ;
/** @type {__VLS_StyleScopedClasses['floating-nav']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.a, __VLS_intrinsics.a)({
    ...{ class: "brand" },
    href: "#hero",
});
/** @type {__VLS_StyleScopedClasses['brand']} */ ;
(__VLS_ctx.settings.nav_brand);
__VLS_asFunctionalElement1(__VLS_intrinsics.nav, __VLS_intrinsics.nav)({
    'aria-label': "主导航",
});
__VLS_asFunctionalElement1(__VLS_intrinsics.a, __VLS_intrinsics.a)({
    href: "#hero",
});
__VLS_asFunctionalElement1(__VLS_intrinsics.a, __VLS_intrinsics.a)({
    href: "#articles",
});
__VLS_asFunctionalElement1(__VLS_intrinsics.a, __VLS_intrinsics.a)({
    href: "#about",
});
__VLS_asFunctionalElement1(__VLS_intrinsics.a, __VLS_intrinsics.a)({
    href: "#timeline",
});
__VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
    id: "hero",
    ...{ class: "hero" },
    ...{ style: ({ backgroundImage: `linear-gradient(rgba(7, 18, 29, 0.38), rgba(7, 18, 29, 0.72)), url(${__VLS_ctx.settings.hero_image_url})` }) },
});
/** @type {__VLS_StyleScopedClasses['hero']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "hero-atmosphere" },
    'aria-hidden': "true",
});
/** @type {__VLS_StyleScopedClasses['hero-atmosphere']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "hero-route" },
    'aria-hidden': "true",
});
/** @type {__VLS_StyleScopedClasses['hero-route']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
    ...{ class: "route-point" },
});
/** @type {__VLS_StyleScopedClasses['route-point']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "hero-overlay" },
});
/** @type {__VLS_StyleScopedClasses['hero-overlay']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "hero-subtitle" },
});
/** @type {__VLS_StyleScopedClasses['hero-subtitle']} */ ;
(__VLS_ctx.settings.site_subtitle);
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "quote-box" },
});
/** @type {__VLS_StyleScopedClasses['quote-box']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "quote-line" },
});
/** @type {__VLS_StyleScopedClasses['quote-line']} */ ;
(__VLS_ctx.typedQuote);
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
    ...{ class: "cursor" },
});
/** @type {__VLS_StyleScopedClasses['cursor']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "quote-author" },
});
/** @type {__VLS_StyleScopedClasses['quote-author']} */ ;
(__VLS_ctx.activeQuote.author);
__VLS_asFunctionalElement1(__VLS_intrinsics.a, __VLS_intrinsics.a)({
    ...{ class: "scroll-indicator" },
    href: "#articles",
    'aria-label': "继续往下看",
    title: "继续往下看",
});
/** @type {__VLS_StyleScopedClasses['scroll-indicator']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
    ...{ class: "scroll-arrow" },
    'aria-hidden': "true",
});
/** @type {__VLS_StyleScopedClasses['scroll-arrow']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.main, __VLS_intrinsics.main)({
    ...{ class: "content-shell" },
});
/** @type {__VLS_StyleScopedClasses['content-shell']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
    id: "articles",
    ...{ class: "content-section feature-grid" },
});
/** @type {__VLS_StyleScopedClasses['content-section']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-grid']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.article, __VLS_intrinsics.article)({
    ...{ class: "feature-card feature-card-accent" },
});
/** @type {__VLS_StyleScopedClasses['feature-card']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-card-accent']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "section-tag" },
});
/** @type {__VLS_StyleScopedClasses['section-tag']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.article, __VLS_intrinsics.article)({
    ...{ class: "feature-card" },
});
/** @type {__VLS_StyleScopedClasses['feature-card']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "section-tag" },
});
/** @type {__VLS_StyleScopedClasses['section-tag']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.article, __VLS_intrinsics.article)({
    ...{ class: "feature-card" },
});
/** @type {__VLS_StyleScopedClasses['feature-card']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "section-tag" },
});
/** @type {__VLS_StyleScopedClasses['section-tag']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
    id: "about",
    ...{ class: "content-section split-section" },
});
/** @type {__VLS_StyleScopedClasses['content-section']} */ ;
/** @type {__VLS_StyleScopedClasses['split-section']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "section-tag" },
});
/** @type {__VLS_StyleScopedClasses['section-tag']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "glass-panel" },
});
/** @type {__VLS_StyleScopedClasses['glass-panel']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.ul, __VLS_intrinsics.ul)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.li, __VLS_intrinsics.li)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.li, __VLS_intrinsics.li)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.li, __VLS_intrinsics.li)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.section, __VLS_intrinsics.section)({
    id: "timeline",
    ...{ class: "content-section timeline-section" },
});
/** @type {__VLS_StyleScopedClasses['content-section']} */ ;
/** @type {__VLS_StyleScopedClasses['timeline-section']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "section-tag" },
});
/** @type {__VLS_StyleScopedClasses['section-tag']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "timeline" },
});
/** @type {__VLS_StyleScopedClasses['timeline']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "timeline-item" },
});
/** @type {__VLS_StyleScopedClasses['timeline-item']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "timeline-item" },
});
/** @type {__VLS_StyleScopedClasses['timeline-item']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "timeline-item" },
});
/** @type {__VLS_StyleScopedClasses['timeline-item']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({});
// @ts-ignore
[navVisible, navRevealing, settings, settings, settings, typedQuote, activeQuote,];
const __VLS_export = (await import('vue')).defineComponent({});
export default {};

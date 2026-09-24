const assert = require("node:assert/strict");
const { chromium } = require("playwright");

// 使用合成资料覆盖接口数量和长文本，不依赖本地或线上数据库内容。
// 运行前启动前台；Playwright 不在仓库依赖中时，通过 NODE_PATH 指向本机安装。
const baseUrl = process.env.ABOUT_CHECK_URL || "http://localhost:5173/about";
const emptyProfile = {
  id: 0, display_name: "", role: "", headline: "", bio: "", avatar_url: "",
  resume_url: "", resume_filename: "", status_text: "", email: null,
  location_name: "", location_longitude: null, location_latitude: null,
  metrics: [], work_experiences: [], project_experiences: [], skills: [],
  social_links: [], interests: [], site_title: "", site_description: "",
  site_launched_at: "", site_stack: [], site_repository_url: null, updated_at: "",
};
function fixture({ long = false } = {}) {
  const technologies = ["Vue 3", "TypeScript", "Python", "PostgreSQL"];
  return {
    ...emptyProfile,
    id: 1,
    display_name: long ? "保持好奇的独立开发者" : "测试航海员",
    role: "全栈工程师 / 产品探索者",
    headline: "把灵感做成可以使用的作品，持续探索技术与生活。",
    bio: "这是一份用于页面验收的合成资料。关注可维护的软件、清晰的交互，以及屏幕之外的生活。".repeat(long ? 6 : 2),
    status_text: "正在探索下一段航程",
    resume_url: new URL("/__about_test_resume", baseUrl).href,
    resume_filename: "测试简历.pdf",
    email: long ? "independent-developer-and-product-explorer@example.test" : "hello@example.test",
    location_name: long ? "一个用于检查长地名换行的海边城市" : "海边城市",
    metrics: Array.from({ length: 5 }, (_, index) => ({ value: `${index + 2}+`, label: `实践指标 ${index + 1}` })),
    work_experiences: Array.from({ length: 3 }, (_, index) => ({
      organization: long ? `第 ${index + 1} 站 · 持续探索产品设计与工程实践的团队` : `探索团队 ${index + 1}`,
      role: "产品工程师", period: `${2020 + index} — ${2021 + index}`,
    })),
    project_experiences: Array.from({ length: 7 }, (_, index) => ({
      name: long ? `项目 ${index + 1} · 支持多平台协作与持续交付的产品工作台` : `测试作品 ${index + 1}`,
      role: "设计与开发", period: `202${index} — 202${index + 1}`,
      summary: "将真实需求转化为可维护的产品，负责界面设计、数据服务和交互实现。".repeat(long ? 8 : 2),
      link_url: "https://example.test/project",
      technologies: [technologies[index % technologies.length]],
    })),
    skills: technologies.map((name) => ({ name, icon_url: "" })),
    social_links: [{ platform: "GitHub", label: "代码仓库", url: "https://example.test/source" }],
    interests: ["摄影", "阅读", "旅行", "徒步"],
    site_title: "关于这个航海日志", site_description: "记录技术实践和生活里的观察。",
    site_launched_at: "2024", site_stack: ["Vue 3", "TypeScript", "Python"],
    site_repository_url: "https://example.test/source", updated_at: "2026-09-01T00:00:00Z",
  };
}
const envelope = (data) => ({ code: 200, status: 200, message: "ok", request_id: "about-ui-check", data });
const checked = [];
const diagnostics = [];
async function createPage(browser, profile, options = {}) {
  const context = await browser.newContext({ viewport: options.viewport || { width: 1440, height: 1000 }, reducedMotion: options.reducedMotion || "no-preference" });
  const page = await context.newPage();
  const errors = [];
  const consoleErrors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() !== "error") return;
    const url = message.location().url;
    // HTTP 503 是错误重试用例有意制造的响应。
    if (options.failFirst && url.includes("/about-profile") && message.text().includes("503")) return;
    consoleErrors.push(`${message.text()} ${url}`.trim());
  });
  let requests = 0;
  await page.route("**/api/v1/about-profile", (route) => {
    requests++;
    return route.fulfill({
      status: options.failFirst && requests === 1 ? 503 : 200,
      contentType: "application/json",
      body: JSON.stringify(options.failFirst && requests === 1 ? { code: 503, status: 503, message: "test retry", data: null } : envelope(profile)),
    });
  });
  await page.route("**/__about_test_resume", (route) => route.fulfill({ contentType: "text/html", body: "<!doctype html><html lang='zh-CN'><title>测试简历</title><p>合成简历预览</p></html>" }));
  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await page.locator("main[aria-busy='false']").waitFor();
  return {
    page,
    requests: () => requests,
    async close(label) {
      assert.deepEqual(errors, [], `${label}: 页面执行错误`);
      assert.deepEqual(consoleErrors, [], `${label}: 控制台错误`);
      await context.close();
      checked.push(label);
    },
  };
}
async function selectedProject(page, index, profile) {
  const tabs = page.getByRole("tab");
  await page.waitForFunction((index) => document.querySelectorAll('[role="tab"]')[index]?.getAttribute("aria-selected") === "true", index);
  assert.equal(await tabs.nth(index).getAttribute("tabindex"), "0");
  assert.equal(await page.locator('[role="tab"][aria-selected="true"]').count(), 1);
  await page.getByRole("tabpanel").getByRole("heading", { name: profile.project_experiences[index].name, exact: true }).waitFor();
  assert.equal(await page.getByLabel("当前项目技术栈").innerText(), profile.project_experiences[index].technologies[0]);
  const related = await page.locator(".skills-ledger li").filter({ hasText: "当前项目使用" }).innerText();
  assert.ok(related.includes(profile.project_experiences[index].technologies[0]), "项目切换应联动工具箱高亮");
}
async function settleScroll(page, top) {
  await page.evaluate((y) => window.scrollTo({ top: y, behavior: "instant" }), top);
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
}
async function noOverflow(page, label) {
  // 入场位移的中间帧可以临时超过布局盒；待有限动画结束再判断正文溢出。
  await page.evaluate(() => Promise.all(document.getAnimations()
    .filter((animation) => Number.isFinite(animation.effect.getTiming().iterations))
    .map((animation) => animation.finished.catch(() => {}))));
  const result = await page.evaluate(() => ({
    viewport: innerWidth,
    document: document.documentElement.scrollWidth,
    overflowing: Array.from(document.querySelectorAll(".hero-copy,.section-heading,.project-dossier,.profile-copy,.journey-list,.life-copy,.port-card,.site-copy,.contact-copy,.contact-postcard"))
      .filter((element) => element.scrollWidth > element.clientWidth + 2)
      .map((element) => ({ className: element.className, content: element.scrollWidth, width: element.clientWidth })),
  }));
  diagnostics.push({ label, ...result });
  assert.ok(result.document <= result.viewport + 1, `${label}: 页面横向溢出 ${JSON.stringify(result)}`);
  assert.deepEqual(result.overflowing, [], `${label}: 内容容器横向溢出`);
}
async function interactions(browser) {
  const profile = fixture();
  const test = await createPage(browser, profile);
  const { page } = test;
  assert.equal(await page.getByRole("tab").count(), profile.project_experiences.length);
  await selectedProject(page, 0, profile);
  await page.getByRole("tab").nth(2).click();
  await selectedProject(page, 2, profile);
  await page.getByRole("tab").nth(2).press("End");
  await selectedProject(page, 6, profile);
  assert.equal(await page.getByRole("tab").nth(6).evaluate((element) => element === document.activeElement), true);
  await page.getByRole("tab").nth(6).press("ArrowRight");
  await selectedProject(page, 0, profile);
  await page.getByRole("tab").nth(0).press("End");
  await page.getByRole("tab").nth(6).press("Home");
  await selectedProject(page, 0, profile);
  await page.getByRole("button", { name: "上一个项目", exact: true }).click();
  await selectedProject(page, 6, profile);
  await page.getByRole("button", { name: "下一个项目", exact: true }).click();
  await selectedProject(page, 0, profile);

  const preview = page.getByRole("button", { name: "预览简历", exact: true });
  await preview.click();
  await page.getByRole("dialog").waitFor();
  assert.equal(await page.getByTitle("在线预览简历").count(), 1);
  await page.keyboard.press("Escape");
  await page.getByRole("dialog").waitFor({ state: "hidden" });
  await page.getByTitle("在线预览简历").waitFor({ state: "detached" });
  assert.equal(await page.getByTitle("在线预览简历").count(), 0, "关闭预览应卸载 iframe");
  assert.equal(await preview.evaluate((element) => element === document.activeElement), true, "关闭后应恢复按钮焦点");

  await page.getByRole("button", { name: "翻到背面 · 微信联系" }).click();
  await page.getByAltText("微信联系二维码").waitFor();
  assert.equal(await page.getByRole("button", { name: "返回明信片" }).getAttribute("aria-expanded"), "true");
  await page.getByRole("button", { name: "返回明信片" }).click();
  await page.getByAltText("海岸旅行主题插画").waitFor();
  assert.equal(await page.getByAltText("微信联系二维码").count(), 0);

  await settleScroll(page, 0);
  const initial = await page.locator(".night-hero").evaluate((element) => getComputedStyle(element).getPropertyValue("--scene-progress"));
  await settleScroll(page, 280);
  await page.waitForFunction((before) => getComputedStyle(document.querySelector(".night-hero")).getPropertyValue("--scene-progress") !== before, initial);
  const seaBefore = await page.locator(".hero-seascape img").evaluate((element) => getComputedStyle(element).transform);
  await settleScroll(page, 430);
  await page.waitForFunction((before) => getComputedStyle(document.querySelector(".hero-seascape img")).transform !== before, seaBefore);
  const journeyTop = await page.locator("#about-journey").evaluate((element) => element.getBoundingClientRect().top + scrollY);
  await settleScroll(page, journeyTop - 600);
  const bearingBefore = await page.locator(".journey-bearing svg").evaluate((element) => getComputedStyle(element).transform);
  await settleScroll(page, journeyTop);
  await page.waitForFunction((before) => getComputedStyle(document.querySelector(".journey-bearing svg")).transform !== before, bearingBefore);
  assert.equal(await page.locator(".workbench-float").evaluate((element) => getComputedStyle(element).animationPlayState), "paused", "离屏首屏应暂停循环动效");

  await page.getByRole("tabpanel").scrollIntoViewIfNeeded();
  const card = await page.getByRole("tabpanel").boundingBox();
  await page.mouse.move(card.x + card.width * 0.85, card.y + card.height * 0.3);
  await page.waitForFunction(() => Number.parseFloat(document.querySelector('[role="tabpanel"]').style.getPropertyValue("--card-x")) > 0);
  await page.getByRole("button", { name: "暂停动效", exact: true }).click();
  await page.locator("main.motion-paused").waitFor();
  assert.equal(await page.locator(".hero-workbench").evaluate((element) => getComputedStyle(element).transform), "none");
  assert.equal(await page.locator(".workbench-float").evaluate((element) => getComputedStyle(element).animationPlayState), "paused");
  assert.equal(await page.getByRole("button", { name: "开启动效", exact: true }).getAttribute("aria-pressed"), "true");
  await noOverflow(page, "桌面");
  await page.getByRole("button", { name: "开启动效", exact: true }).click();
  await page.locator("main:not(.motion-paused)").waitFor();
  await test.close("项目、简历、明信片、滚动与指针动效、暂停及离屏暂停");
}
async function responsive(browser) {
  for (const width of [390, 320, 768]) {
    const profile = fixture({ long: true });
    const test = await createPage(browser, profile, { viewport: { width, height: 844 }, reducedMotion: "reduce" });
    await noOverflow(test.page, `${width}px 长资料`);
    await test.page.getByRole("tab").first().focus();
    await test.page.getByRole("tab").first().press("End");
    await selectedProject(test.page, 6, profile);
    const selectedVisible = await test.page.getByRole("tab").nth(6).evaluate((element) => {
      const tab = element.getBoundingClientRect();
      const list = element.parentElement.getBoundingClientRect();
      return tab.left >= list.left - 2 && tab.right <= list.right + 2;
    });
    assert.ok(selectedVisible, `${width}px: 键盘选中项目应进入可视范围`);
    await noOverflow(test.page, `${width}px 切换后`);
    await test.close(`${width}px 响应式及长资料`);
  }
}
async function states(browser) {
  const reduced = await createPage(browser, fixture(), { reducedMotion: "reduce" });
  await reduced.page.locator("main.motion-paused").waitFor();
  assert.equal(await reduced.page.getByRole("button", { name: "暂停动效", exact: true }).count(), 0);
  assert.equal(await reduced.page.locator(".hero-workbench").evaluate((element) => getComputedStyle(element).transform), "none");
  assert.equal(await reduced.page.locator("[data-about-reveal]:not(.is-revealed)").count(), 0, "减少动态下全部内容应可读");
  await reduced.close("系统减少动态偏好");

  const empty = await createPage(browser, emptyProfile);
  assert.equal(await empty.page.getByRole("tab").count(), 0);
  assert.equal(await empty.page.getByRole("button", { name: "预览简历", exact: true }).count(), 0);
  await empty.page.getByText("项目档案正在整理中。", { exact: true }).waitFor();
  assert.equal(await empty.page.locator("#about-life").count(), 0);
  await noOverflow(empty.page, "空资料");
  await empty.close("空资料降级");

  const retry = await createPage(browser, fixture(), { failFirst: true });
  await retry.page.getByText("个人资料暂时无法加载，请稍后重试。", { exact: false }).waitFor();
  await retry.page.getByRole("button", { name: "重新加载", exact: true }).click();
  await retry.page.getByRole("tab").first().waitFor();
  assert.equal(retry.requests(), 2);
  assert.equal(await retry.page.getByRole("button", { name: "重新加载", exact: true }).count(), 0);
  await retry.close("接口失败与重试恢复");
}
(async () => {
  const browser = await chromium.launch({ channel: "chrome", headless: true });
  try {
    await interactions(browser);
    await responsive(browser);
    await states(browser);
    console.log(JSON.stringify({ passed: checked, viewports: diagnostics }, null, 2));
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });

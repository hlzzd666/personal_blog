const { chromium } = require("playwright");
const assert = require("node:assert/strict");
const base = process.env.IMAGE_CHECK_URL || "http://127.0.0.1:5176";
const broken = base + "/broken.jpg",
  good = base + "/good.svg";
const article = {
  id: 1,
  title: "图片测试",
  slug: "image-test",
  summary: "测试摘要",
  content_markdown: "# 测试",
  cover_image_url: broken,
  author: "测试",
  category: "随笔",
  tags: [],
  tag_ids: [],
  category_id: null,
  series_id: null,
  series_order: null,
  is_repost: false,
  source_url: null,
  views: 0,
  likes: 0,
  published_at: "2026-01-01T00:00:00",
  updated_at: "2026-01-01T00:00:00",
};
const settings = {
  site_subtitle: "测试站点",
  hero_image_url: broken,
  nav_brand: "测试",
  dashboard_years: [2026],
  quotes: [],
  visual_assets: [
    {
      key: "background",
      name: "背景图",
      usage: "background",
      image_url: broken,
      enabled: true,
      opacity: 0.68,
      note: "",
    },
  ],
  owner_avatar_url: "",
  owner_location_name: "测试",
  site_launched_on: "2026-01-01",
};
(async () => {
  const browser = await chromium.launch({ headless: true, channel: "chrome" });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  let failUpload = true,
    saved = null;
  await page.route("**/broken.jpg", (r) => r.fulfill({ status: 403, body: "blocked" }));
  await page.route("**/good.svg", (r) =>
    r.fulfill({
      contentType: "image/svg+xml",
      body: '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200"><rect width="400" height="200" fill="teal"/></svg>',
    }),
  );
  await page.route("**/api/v1/**", async (r) => {
    const url = new URL(r.request().url());
    let data;
    if (url.pathname.endsWith("/auth/me"))
      data = { username: "qa", logged_in_at: "2026-01-01", expires_at: "2027-01-01" };
    else if (url.pathname.endsWith("/site-settings")) data = settings;
    else if (url.pathname.endsWith("/articles/manage"))
      data = { items: [article], total: 1, page: 1, page_size: 20 };
    else if (url.pathname.endsWith("/article-taxonomy"))
      data = { categories: [{ id: 1, name: "随笔" }], tags: [] };
    else if (url.pathname.endsWith("/series")) data = { items: [], total: 0 };
    else if (url.pathname.endsWith("/media/images")) {
      if (failUpload)
        return r.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ code: 500, status: 500, message: "测试上传失败" }),
        });
      data = { url: good, filename: "good.svg", size: 100, content_type: "image/svg+xml" };
    } else if (url.pathname.endsWith("/articles/1")) {
      saved = r.request().postDataJSON();
      data = { ...article, ...saved };
    } else data = {};
    await r.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ code: 200, status: 200, message: "ok", data }),
    });
  });
  await page.goto(base + "/site-settings");
  await page.getByText("图片加载失败", { exact: true }).first().waitFor();
  assert.equal(await page.locator(".visual-asset-preview .image-preview-error").count(), 1);
  await page.locator(".visual-asset-form input").nth(3).fill(good);
  await page.waitForFunction(
    () => document.querySelector(".visual-asset-preview img")?.naturalWidth > 0,
  );
  await page.screenshot({ path: ".codex-screenshots/images-settings.png", fullPage: true });
  await page.goto(base + "/articles");
  await page.getByRole("button", { name: "编辑", exact: true }).first().click();
  const cover = page
    .locator(".el-form-item")
    .filter({ has: page.getByText("封面图 URL", { exact: true }) });
  await cover.locator("input:not([type=file])").waitFor();
  assert.equal(await cover.locator("input:not([type=file])").inputValue(), broken);
  const file = {
    name: "original.gif",
    mimeType: "image/gif",
    buffer: Buffer.from("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7", "base64"),
  };
  await cover.locator("input[type=file]").setInputFiles(file);
  await page.getByText("测试上传失败", { exact: true }).waitFor();
  assert.equal(await cover.locator("input:not([type=file])").inputValue(), broken);
  failUpload = false;
  await cover.locator("input[type=file]").setInputFiles(file);
  await page.waitForFunction(
    () => document.querySelector(".editor-cover-preview img")?.naturalWidth > 0,
  );
  assert.equal(await cover.locator("input:not([type=file])").inputValue(), good);
  await cover.scrollIntoViewIfNeeded();
  await page.screenshot({ path: ".codex-screenshots/images-upload.png" });
  await page.getByRole("button", { name: "保存文章", exact: true }).click();
  await page.waitForTimeout(300);
  assert.equal(saved.cover_image_url, good);
  assert.deepEqual(errors, []);
  console.log(
    "PASS: failed preview, URL change recovery, failed upload preserves URL, original upload preview, saved URL; no runtime errors",
  );
  await browser.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});

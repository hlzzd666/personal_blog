const { chromium } = require("playwright");
const assert = require("node:assert/strict");
const base = process.env.MEDIA_CHECK_URL || "http://127.0.0.1:5176";
(async () => {
  const browser = await chromium.launch({ headless: true, channel: "chrome" });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  let partial = false,
    deleted = false;
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const item = (name, storage, referenced) => ({
    filename: name,
    relative_path: name,
    storage,
    cleanup_eligible: true,
    url: base + "/test.svg",
    content_type: "image/svg+xml",
    media_type: "image",
    size: 20,
    modified_at: "2026-11-02T10:00:00",
    referenced,
    references: referenced ? [{ source: "文章", label: "封面" }] : [],
  });
  await page.route("**/test.svg", (r) =>
    r.fulfill({
      contentType: "image/svg+xml",
      body: '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="80"><rect width="100" height="80" fill="teal"/></svg>',
    }),
  );
  await page.route("**/api/v1/**", async (r) => {
    let data;
    const u = new URL(r.request().url());
    if (u.pathname.endsWith("/auth/me"))
      data = { username: "qa", logged_in_at: "2026-01-01", expires_at: "2027-01-01" };
    else if (r.request().method() === "DELETE") {
      assert.equal(u.searchParams.get("storage"), "oss");
      deleted = true;
      data = { deleted_count: 1, deleted_size: 20, deleted_files: ["unused.webp"] };
    } else {
      let items = partial
        ? [{ ...item("used.webp", "oss", true), size: null, modified_at: null }]
        : [
            item("local.webp", "local", true),
            item("used.webp", "oss", true),
            ...(deleted ? [] : [item("unused.webp", "oss", false)]),
          ];
      data = {
        items,
        total: items.length,
        used_count: 2,
        unused_count: 1,
        total_size: 60,
        unused_size: 20,
        warnings: partial ? ["OSS 列表读取失败，当前仅显示已引用资源"] : [],
        oss_complete: !partial,
        upload_storage: "oss",
      };
    }
    await r.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ code: 200, status: 200, data }),
    });
  });
  await page.goto(base + "/media");
  await page.getByText("local.webp", { exact: true }).first().waitFor();
  assert.equal(
    await page.getByRole("button", { name: "清理未引用", exact: true }).isDisabled(),
    true,
  );
  await page.locator(".media-toolbar-filters .el-select").first().click();
  await page.getByRole("option", { name: "OSS", exact: true }).click();
  assert.equal(await page.getByText("local.webp", { exact: true }).count(), 0);
  await page.getByRole("button", { name: "清理 OSS未引用", exact: true }).click();
  await page.getByRole("button", { name: "取消", exact: true }).click();
  assert.equal(deleted, false);
  await page.screenshot({ path: ".codex-screenshots/media-oss.png" });
  await page.getByRole("button", { name: "清理 OSS未引用", exact: true }).click();
  await page.getByRole("button", { name: "确认清理", exact: true }).click();
  await page.getByText("已清理 1 个文件", { exact: false }).waitFor();
  assert(deleted);
  partial = true;
  await page.getByRole("button", { name: "刷新", exact: true }).click();
  await page.getByText("OSS 列表读取失败，当前仅显示已引用资源", { exact: true }).waitFor();
  assert.equal(
    await page.getByRole("button", { name: "清理 OSS未引用", exact: true }).isDisabled(),
    true,
  );
  assert((await page.getByText("未知", { exact: true }).count()) > 0);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: ".codex-screenshots/media-oss-mobile.png" });
  assert.deepEqual(errors, []);
  console.log(
    "PASS storage filter, scoped statistics, confirmed cleanup source, cancel protection, permission fallback, mobile render; no runtime errors",
  );
  await browser.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});

const { chromium } = require("playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const base = process.env.READER_TEST_URL || "http://127.0.0.1:5173";
const output = path.join(os.tmpdir(), "personal-blog-reader-qa");
const notes = Array.from({ length: 14 }, (_, index) => ({
  id: index + 1,
  slug: `navigation-check-${index + 1}`,
  content_markdown: `第 ${index + 1} 条记录：记录开发进度和沿途想法。`.repeat(index % 3 + 1),
  tags: [index % 2 ? "开发" : "日常"],
  published_at: index === 8 ? null : `${index < 4 ? "2026-09" : index < 8 ? "2026-08" : index < 11 ? "2025-08" : "2025-07"}-07T09:00:00`,
  created_at: "2025-08-07T09:00:00",
  updated_at: "2026-09-07T09:00:00",
  external_url: null,
}));

(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ channel: "chrome", headless: true });
  try {
    for (const width of [1192, 390]) {
      const context = await browser.newContext({ viewport: { width, height: 912 } });
      const page = await context.newPage();
      const errors = [];
      let listRequests = 0;
      page.on("pageerror", error => errors.push(error.message));
      // 固定动态数量，覆盖本地只有少量记录时无法验证的长列表返回流程。
      await page.route("**/api/v1/notes**", async route => {
        const url = new URL(route.request().url());
        const slug = url.pathname.split("/")[4];
        const tag = url.searchParams.get("tag");
        const items = notes.filter(note => !tag || note.tags.includes(tag));
        if (!slug) listRequests++;
        const data = slug ? notes.find(note => note.slug === slug) : { items, total: items.length, page: 1, page_size: 100 };
        await route.fulfill({ json: { code: 200, status: 200, message: "ok", data, request_id: "reader-check" } });
      });
      await page.goto(`${base}/notes`, { waitUntil: "domcontentloaded" });
      await page.locator(".note-signal").last().waitFor();
      for (const filtered of [false, true]) {
        if (filtered) {
          await page.getByRole("button", { name: "# 开发", exact: true }).click();
          await page.waitForFunction(() => document.querySelectorAll(".note-signal").length === 7);
        }
        const dividers = await page.locator(".note-signal").evaluateAll(rows => rows.flatMap((row, index) =>
          getComputedStyle(row).borderBottomColor === "rgba(0, 0, 0, 0)" ? [] : [index],
        ));
        assert.deepEqual(dividers, filtered ? [1, 3, 4] : [3, 7, 10], "Only separate different months, including different years");
        const listUrl = page.url();
        for (const back of ["link", "history"]) {
          const link = page.locator(".note-signal footer a").nth(filtered ? 4 : 8);
          await link.scrollIntoViewIfNeeded();
          await page.waitForTimeout(700);
          const y = await page.evaluate(() => window.scrollY);
          const requests = listRequests;
          await link.click();
          await page.locator(".note-document").waitFor();
          await page.waitForFunction(() => window.scrollY === 0);
          if (back === "link") await page.getByRole("link", { name: "返回短动态", exact: true }).click();
          else await page.goBack({ waitUntil: "domcontentloaded" });
          await page.waitForURL(listUrl);
          await page.waitForFunction(target => Math.abs(window.scrollY - target) <= 2, y);
          assert.equal(listRequests, requests, "Returning uses cached list without fetching");
          if (filtered) assert.equal(await page.locator(".notes-tags button.active").innerText(), "# 开发");
          console.log(JSON.stringify({ width, filtered, back, scrollY: y, listRequests }));
        }
      }
      await page.locator(".note-signal").first().scrollIntoViewIfNeeded();
      await page.waitForTimeout(700);
      const gaps = await page.locator(".note-signal-pulse").evaluateAll(pulses => pulses.slice(0, -1).map((pulse, index) => {
        const current = pulse.getBoundingClientRect();
        const next = pulses[index + 1].getBoundingClientRect();
        const line = getComputedStyle(pulse, "::before");
        const nextLine = getComputedStyle(pulses[index + 1], "::before");
        return next.top + parseFloat(nextLine.top) - (current.bottom - parseFloat(line.bottom));
      }));
      assert(gaps.every(gap => Math.abs(gap) <= 1), `Timeline gaps: ${gaps}`);
      await page.screenshot({ path: path.join(output, `notes-${width}.png`) });
      assert.equal(await page.locator(".site-footer a[href*='feed']").count(), 0);
      assert(await page.locator(".site-footer nav a").evaluateAll(links => links.every(link => link.querySelector("img"))));
      await page.locator(".site-footer").scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(output, `footer-${width}.png`) });
      await page.goto(`${base}/articles/python`, { waitUntil: "domcontentloaded" });
      const share = page.locator(".article-share-panel");
      await share.waitFor();
      await share.scrollIntoViewIfNeeded();
      const title = await share.locator("p").boundingBox();
      const description = await share.locator(":scope > div:first-child > span").boundingBox();
      assert(description.y >= title.y + title.height, "Share description sits below title");
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "No horizontal overflow");
      await page.screenshot({ path: path.join(output, `share-${width}.png`) });
      assert.deepEqual(errors, []);
      await context.close();
    }
    console.log(`Reader checks passed. Screenshots: ${output}`);
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });

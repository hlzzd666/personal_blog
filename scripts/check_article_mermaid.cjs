// 使用合成文章做只读回归，不依赖或修改线上数据。
const { chromium } = require("playwright");
const assert = require("node:assert/strict");
const base = process.env.MERMAID_TEST_URL || "http://127.0.0.1:5173";
const fence = (language, source) => `\n\`\`\`${language}\n${source}\n\`\`\`\n`;
const plain = fence("javascript", 'console.log("代码复制检查");');
const valid = fence("mermaid", "flowchart LR\n A[开始调查] --> B[分析问题] --> C[验证结果] --> D[记录证据] --> E[完成调查]");
const invalid = fence("mermaid", "flowchart TD\n A[未闭合");
const unsafe = fence("mermaid", 'flowchart TD\n A["<img src=x onerror=alert(1)>"] --> B[安全终点]\n click B call alert()');
const contents = { plain, valid, mixed: valid + plain + invalid + unsafe + valid };
const envelope = data => ({ code: 200, status: 200, data });

(async () => {
  const browser = await chromium.launch({ channel: "chrome", headless: true });
  try {
    for (const width of [1440, 390]) {
      const context = await browser.newContext({ viewport: { width, height: 1000 } });
      const page = await context.newPage();
      const errors = [];
      const warnings = [];
      const imports = [];
      page.on("pageerror", error => errors.push(error.message));
      page.on("console", message => {
        if (["error", "warning"].includes(message.type())) warnings.push(message.text());
      });
      page.on("request", request => {
        if (/mermaid(?:\.core)?[._-]/.test(request.url())) imports.push(request.url());
      });
      page.on("dialog", dialog => { errors.push("图表触发了脚本"); void dialog.dismiss(); });
      await page.addInitScript(() => {
        window.copiedCode = "";
        Object.defineProperty(navigator, "clipboard", { value: {
          writeText: async value => { window.copiedCode = value; },
        } });
      });
      await page.route("**/api/v1/articles/**", route => {
        const url = new URL(route.request().url());
        const slug = url.pathname.split("/")[4];
        const data = url.pathname.endsWith("/context")
          ? { previous: null, next: { slug: "plain", title: "普通代码文章" }, related: [], series: null }
          : {
            id: 1, slug, title: "流程图回归", content_markdown: contents[slug],
            summary: "合成测试内容", author: "测试", category: "开发", tags: [],
            cover_image_url: null, is_repost: false, views: 0, likes: 0,
            updated_at: "2026-10-15T00:00:00", published_at: null, created_at: "2026-10-15T00:00:00",
          };
        return route.fulfill({ json: envelope(data) });
      });
      await page.goto(`${base}/articles/plain`);
      await page.locator(".md-code-copy").waitFor();
      assert.equal(imports.length, 0, "普通文章不加载 Mermaid");
      await page.goto(`${base}/articles/mixed`);
      await page.waitForFunction(() => document.querySelectorAll(".md-diagram").length === 3);
      await page.locator(".md-diagram-error").waitFor();
      assert.match(await page.title(), /流程图回归/);
      assert.equal(await page.locator("vite-error-overlay").count(), 0);
      assert.equal(await page.locator(".md-mermaid-source .md-code-lang").innerText(), "mermaid");
      assert.match(await page.locator(".md-mermaid-source").innerText(), /未闭合/);
      assert.equal(await page.locator(".md-diagram img, .md-diagram script, .md-diagram [onerror], .md-diagram a").count(), 0);
      const ids = await page.locator(".md-diagram > svg").evaluateAll(nodes => nodes.map(node => node.id));
      assert.equal(new Set(ids).size, 3, "多个图表使用独立 ID");
      await page.locator(".md-diagram").first().scrollIntoViewIfNeeded();
      await page.waitForFunction(() => getComputedStyle(document.querySelector(".md-diagram")).opacity === "1");
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "图表不撑宽页面");
      if (width === 390) {
        const diagram = page.locator(".md-diagram").first();
        await diagram.focus();
        await page.keyboard.press("ArrowRight");
        await page.waitForFunction(() => document.querySelector(".md-diagram").scrollLeft > 0);
      }
      const code = page.locator(".md-code").filter({ has: page.locator(".md-code-lang", { hasText: "javascript" }) });
      assert(await code.locator(".hljs-string").count(), "普通代码仍然高亮");
      await code.locator(".md-code-copy").click();
      await page.waitForFunction(() => window.copiedCode === 'console.log("代码复制检查");');
      assert.match(await code.innerText(), /已复制/);
      await page.getByRole("link", { name: "下一篇 普通代码文章" }).click();
      await page.waitForURL(`${base}/articles/plain`);
      await page.locator(".md-code-copy").waitFor();
      assert.equal(await page.locator(".md-diagram").count(), 0, "切换文章不遗留图表");
      assert.deepEqual(errors, []);
      assert.equal(warnings.length, 1, `只允许无效图表的预期日志：${warnings}`);
      assert.match(warnings[0], /Mermaid 流程图渲染失败/);
      if (width === 1440) {
        let releaseImport;
        const importGate = new Promise(resolve => { releaseImport = resolve; });
        let notifyImport;
        const importStarted = new Promise(resolve => { notifyImport = resolve; });
        await page.route(/mermaid(?:\.core)?[._-]/, async route => {
          notifyImport();
          await importGate;
          await route.continue();
        });
        // 完整导航清空模块缓存，在绘图库下载中切换文章。
        await page.goto(`${base}/articles/valid`, { waitUntil: "domcontentloaded" });
        await importStarted;
        await page.getByRole("link", { name: "下一篇 普通代码文章" }).click();
        await page.waitForURL(`${base}/articles/plain`);
        releaseImport();
        await page.waitForLoadState("networkidle");
        assert.equal(await page.locator(".md-diagram").count(), 0, "过期的异步渲染不写入新文章");
        await page.unroute(/mermaid(?:\.core)?[._-]/);
        await page.route(/mermaid(?:\.core)?[._-]/, route => route.abort());
        await page.goto(`${base}/articles/valid`, { waitUntil: "domcontentloaded" });
        await page.locator(".md-diagram-error").waitFor();
        assert.match(await page.locator(".md-mermaid-source").innerText(), /开始/);
        assert.equal(await page.locator(".article-detail-error").count(), 0, "绘图库下载失败不影响文章");
        assert.deepEqual(errors, []);
      }
      console.log(JSON.stringify({ width, diagrams: ids.length, checks: "passed" }));
      await context.close();
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });

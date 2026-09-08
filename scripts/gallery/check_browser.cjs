const { chromium } = require("playwright");
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const root = path.resolve(__dirname, "../..");
const output = path.join(root, "artifacts/gallery/qa");
fs.mkdirSync(output, { recursive: true });

(async () => {
  const browser = await chromium.launch({
    channel: "chrome",
    headless: true,
    args: ["--enable-webgl", "--ignore-gpu-blocklist"],
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") console.log("BROWSER:", message.text().slice(0, 200));
  });
  await page.goto("http://127.0.0.1:5173/gallery", {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });
  await page.getByRole("button", { name: "进入展馆", exact: true }).waitFor({ timeout: 30000 });
  await page.waitForFunction(() => !document.querySelector("button.primary")?.disabled);
  await page.screenshot({ path: path.join(output, "desktop-entry.png") });
  const enterBounds = await page
    .getByRole("button", { name: "进入展馆", exact: true })
    .boundingBox();
  await page.getByRole("button", { name: "进入展馆", exact: true }).click();
  await page.waitForTimeout(800);
  const locked = await page.evaluate(() => Boolean(document.pointerLockElement));
  assert(locked, "Real Pointer Lock should be active");
  await page.keyboard.down("w");
  await page.waitForFunction(
    () => {
      const marker = document.querySelector(".gallery-minimap svg g");
      if (!marker) return false;
      const y = marker.transform.baseVal.getItem(0).matrix.f;
      return -27.7 + ((y - 18) / 224) * 36.4 < 0.2;
    },
    null,
    { timeout: 20000 },
  );
  await page.keyboard.up("w");
  await page.mouse.move(
    enterBounds.x + enterBounds.width / 2 + 110,
    enterBounds.y + enterBounds.height / 2,
  );
  await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(output, "desktop-tour.png") });
  await page.evaluate(() => {
    const angle = document
      .querySelector(".gallery-minimap svg g")
      .transform.baseVal.getItem(1).angle;
    document.dispatchEvent(
      new MouseEvent("mousemove", {
        movementX: Math.round(((-90 - angle) * Math.PI) / 180 / 0.002),
        movementY: 0,
        bubbles: true,
      }),
    );
  });
  await page.locator(".gallery-active-prompt").waitFor();
  await page.keyboard.press("e");
  await page.locator("dialog[open]").waitFor();
  await page.screenshot({ path: path.join(output, "desktop-3d-detail.png") });
  await page.getByRole("button", { name: "关闭", exact: true }).click();
  assert(await page.evaluate(() => Boolean(document.pointerLockElement)));
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "人物档案", exact: true }).click();
  await page.getByRole("button", { name: "查看蒙奇·D·路飞档案" }).click();
  await page.locator("dialog[open]").waitFor();
  await page.screenshot({ path: path.join(output, "desktop-detail.png") });
  await page.getByRole("button", { name: "关闭", exact: true }).click();
  assert.equal(
    await page.evaluate(() => Boolean(document.pointerLockElement)),
    false,
    "2D detail must not acquire pointer lock",
  );
  const data = await page.evaluate(
    async () => (await (await fetch("/api/v1/gallery")).json()).data,
  );
  const mobile = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
    deviceScaleFactor: 1,
  });
  const phone = await mobile.newPage();
  await phone.goto("http://127.0.0.1:5173/gallery", { waitUntil: "domcontentloaded" });
  await phone.locator(".fallback-item").first().waitFor();
  assert.equal(await phone.locator("canvas.gallery-canvas").count(), 0);
  assert.equal(await phone.locator(".fallback-item").count(), data.characters.length);
  assert(await phone.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await phone.screenshot({ path: path.join(output, "mobile.png"), fullPage: true });
  await phone.getByRole("button", { name: "查看蒙奇·D·路飞档案" }).click();
  await phone.screenshot({ path: path.join(output, "mobile-detail.png") });
  await phone.getByRole("button", { name: "关闭", exact: true }).click();

  // Exercise isolated scene instances using the actual public data, without writing the database.
  await page.goto("http://127.0.0.1:5173/gallery", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "人物档案", exact: true }).click();
  const cases = [];
  for (const count of [0, 1, 12, 40]) {
    const result = await page.evaluate(
      async ({ count, data }) => {
        const { GalleryScene } = await import("/src/gallery/GalleryScene.ts");
        const { isWalkable } = await import("/src/gallery/layout.ts");
        const container = document.createElement("div");
        Object.assign(container.style, { position: "fixed", inset: "0", zIndex: "99999" });
        document.body.append(container);
        const characters = Array.from({ length: count }, (_, i) => ({
          ...data.characters[i % data.characters.length],
          id: i + 1,
          sort_order: i,
          ...(count === 40
            ? { poster_url: data.characters[0].poster_url + "?gallery_qa=" + i }
            : {}),
        }));
        let navigation, active;
        window.fixture = new GalleryScene(container, characters, false, {
          onActiveCharacter: (c) => (active = c),
          onLockChange: () => {},
          onOpenCharacter: (c) => (window.openedId = c.id),
          onNavigation: (s) => (navigation = s),
          onUnavailable: (r) => (window.fixtureError = r),
        });
        const fixture = window.fixture;
        await fixture.ready;
        fixture.camera.position.set(-2.1, 1.7, 0);
        fixture.camera.lookAt(-4.35, 2.05, 0);
        await new Promise((r) => setTimeout(r, 1200));
        const sceneStats = {
          count,
          exhibits: fixture.exhibits.length,
          bays: fixture.hall.bays,
          draws: fixture.renderer.info.render.calls,
          triangles: fixture.renderer.info.render.triangles,
          textures: fixture.renderer.info.memory.textures,
          posters: fixture.posterCache.size,
          maps: fixture.exhibits.map((e) => e.poster.map !== e.fallback),
          modules: fixture.scene.children.filter((c) => c.name === "CabinBay").length,
        };
        const gl = fixture.renderer.getContext(),
          pixels = new Uint8Array(gl.drawingBufferWidth * gl.drawingBufferHeight * 4);
        fixture.renderer.render(fixture.scene, fixture.camera);
        gl.readPixels(
          0,
          0,
          gl.drawingBufferWidth,
          gl.drawingBufferHeight,
          gl.RGBA,
          gl.UNSIGNED_BYTE,
          pixels,
        );
        sceneStats.pixelColors = new Set(
          Array.from(
            { length: Math.floor(pixels.length / 4096) },
            (_, i) => `${pixels[i * 4096]},${pixels[i * 4096 + 1]},${pixels[i * 4096 + 2]}`,
          ),
        ).size;
        sceneStats.boundaries =
          !isWalkable(5, 0, fixture.hall) &&
          !isWalkable(0, fixture.hall.minZ - 1, fixture.hall) &&
          !isWalkable(0, fixture.hall.cabinFront - 5.8, fixture.hall);
        sceneStats.entryWalkable = isWalkable(0, 5.8, fixture.hall);
        window.fixtureNavigation = () => navigation;
        window.fixtureActive = () => active;
        return sceneStats;
      },
      { count, data },
    );
    assert.equal(result.exhibits, count);
    assert(result.pixelColors > 8);
    assert(result.boundaries);
    assert(result.entryWalkable);
    assert(result.posters <= 12);
    if (count) {
      await page.evaluate(() => {
        const button = document.createElement("button");
        button.id = "fixture-lock";
        button.textContent = "Lock fixture";
        Object.assign(button.style, {
          position: "fixed",
          top: "10px",
          left: "10px",
          zIndex: "100000",
        });
        button.onclick = () => window.fixture.lock();
        document.body.append(button);
      });
      await page.locator("#fixture-lock").click();
      await page.waitForTimeout(200);
      assert(
        await page.evaluate(() => Boolean(window.fixtureActive())),
        "Facing a nearby exhibit activates it",
      );
      await page.keyboard.press("e");
      assert.equal(await page.evaluate(() => window.openedId), 1);
      const before = await page.evaluate(() => ({
        x: window.fixture.camera.position.x,
        z: window.fixture.camera.position.z,
      }));
      await page.keyboard.down("ArrowUp");
      await page.waitForTimeout(350);
      await page.keyboard.up("ArrowUp");
      const after = await page.evaluate(() => ({
        x: window.fixture.camera.position.x,
        z: window.fixture.camera.position.z,
      }));
      assert(Math.hypot(after.x - before.x, after.z - before.z) > 0.2);
      await page.mouse.click(720, 500);
      assert.equal(await page.evaluate(() => window.openedId), 1);
      await page.keyboard.press("Escape");
      await page.locator("#fixture-lock").evaluate((e) => e.remove());
    }
    await page.evaluate(() => {
      window.fixture.camera.position.set(0, 1.7, 5.8);
      window.fixture.camera.lookAt(0, 1.7, -10);
    });
    await page.waitForTimeout(250);
    await page.screenshot({ path: path.join(output, `capacity-${count}.png`) });
    if (count === 40) {
      result.performance = await page.evaluate(async () => {
        const durations = [];
        let last = performance.now();
        const started = last;
        while (performance.now() - started < 15000)
          await new Promise((resolve) =>
            requestAnimationFrame((now) => {
              durations.push(now - last);
              last = now;
              const phase = Math.min((now - started) / 15000, 1);
              const travel = 1 - Math.abs(phase * 2 - 1);
              window.fixture.camera.position.z = 5.8 - (5.8 - window.fixture.hall.cabinFront - 1.7) * travel;
              resolve();
            }),
          );
        const gl = window.fixture.renderer.getContext(),
          ext = gl.getExtension("WEBGL_debug_renderer_info");
        durations.sort((a, b) => a - b);
        return {
          frames: durations.length,
          durationMs: last - started,
          averageFps: 1000 / (durations.reduce((a, b) => a + b, 0) / durations.length),
          p95FrameMs: durations[Math.floor(durations.length * .95)],
          renderer: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : "unknown",
          viewport: [innerWidth, innerHeight],
          draws: window.fixture.renderer.info.render.calls,
        };
      });
      result.eviction = await page.evaluate(async () => {
        const fixture = window.fixture;
        fixture.camera.position.set(0, 1.7, fixture.hall.cabinFront + 2);
        fixture.camera.lookAt(0, 1.7, fixture.hall.cabinFront - 10);
        await new Promise((r) => setTimeout(r, 1500));
        return {
          cached: fixture.posterCache.size,
          firstIsPlaceholder: fixture.exhibits[0].poster.map === fixture.exhibits[0].fallback,
          finalIsLoaded: fixture.exhibits.at(-1).poster.map !== fixture.exhibits.at(-1).fallback,
        };
      });
      assert(result.eviction.cached <= 12);
      assert(result.eviction.firstIsPlaceholder);
      assert(result.eviction.finalIsLoaded);
    }
    await page.evaluate(() => {
      const container = window.fixture.container;
      window.fixture.dispose();
      window.fixture = null;
      container.remove();
    });
    cases.push(result);
  }
  for (const mode of ["webgl", "pointer", "model", "api", "empty", "broken-poster"]) {
    const fallbackContext = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const tab = await fallbackContext.newPage();
    if (mode === "webgl")
      await tab.addInitScript(() => {
        const get = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function (type, ...args) {
          return type === "webgl2" ? null : get.call(this, type, ...args);
        };
      });
    if (mode === "pointer")
      await tab.addInitScript(() => {
        Element.prototype.requestPointerLock = function () {
          document.dispatchEvent(new Event("pointerlockerror"));
          return Promise.reject(new Error("denied for test"));
        };
      });
    if (mode === "model") await tab.route("**/flagship.glb", (route) => route.abort());
    if (mode === "api")
      await tab.route("**/api/v1/gallery", (route) =>
        route.fulfill({ status: 503, body: "unavailable" }),
      );
    if (mode === "empty" || mode === "broken-poster")
      await tab.route("**/api/v1/gallery", (route) =>
        route.fulfill({
          json: {
            code: 200,
            status: 200,
            data: {
              ...data,
              characters:
                mode === "empty"
                  ? []
                  : [{ ...data.characters[0], poster_url: "/uploads/missing-test.png" }],
            },
          },
        }),
      );
    await tab.goto("http://127.0.0.1:5173/gallery", { waitUntil: "domcontentloaded" });
    if (mode === "pointer" || mode === "empty")
      await tab.getByRole("button", { name: "进入展馆", exact: true }).click();
    if (["webgl", "pointer", "model"].includes(mode))
      await tab.locator(".gallery-fallback").waitFor();
    if (mode === "api") await tab.getByRole("button", { name: "重新读取" }).waitFor();
    if (mode === "empty") assert(await tab.evaluate(() => Boolean(document.pointerLockElement)));
    if (mode === "broken-poster") {
      await tab.getByRole("button", { name: "人物档案", exact: true }).click();
      await tab.getByRole("button", { name: `查看${data.characters[0].name}档案` }).click();
      assert(await tab.locator(".dialog-poster .poster-placeholder").isVisible());
    }
    await fallbackContext.close();
  }
  assert.deepEqual(errors, []);
  const report = {
    realPublicCharacters: data.characters.length,
    pointerLock: true,
    cases,
    fallbacks: ["webgl", "pointer", "model", "api", "empty", "broken-poster"],
    errors,
  };
  fs.writeFileSync(path.join(output, "browser-report.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exit(1);
});

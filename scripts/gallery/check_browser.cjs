// 确定性只读回归：不依赖开发数据库，截图和报告默认写到临时目录。
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const base = process.env.GALLERY_URL || 'http://127.0.0.1:5173';
const output = process.env.GALLERY_QA_OUTPUT || path.join(os.tmpdir(), 'gallery-museum-qa');
fs.mkdirSync(output, { recursive: true });
const names = ['蒙奇·D·路飞', '罗罗诺亚·索隆', '娜美', '乌索普', '山治', '乔巴', '妮可·罗宾', '弗兰奇', '甚平'];
const data = {
  settings: { id: 1, hall_name: '伟大航路人物档案馆', entry_title: '人物展馆', show_entry: true, show_logo: false, logo_url: null },
  chapters: ['东海群像', '伟大航路', '新世界'].map((title, i) => ({ id: i + 1, title, subtitle: '航海章节', heading: title, description: '章节说明', note: '查阅本章人物', label: '人物故事', story: '章节故事', artwork_index: i + 1, is_visible: true, sort_order: i })),
  characters: names.map((name, i) => ({ id: i + 1, chapter_id: i < 5 ? 1 : i < 8 ? 2 : 3, name, epithet: '航海者', faction: '草帽一伙', bounty: '档案记录', ability: '测试能力', description: '公开人物履历。', quote: '向着梦想启航。', poster_url: null, is_visible: true, sort_order: i })),
};
const envelope = value => ({ code: 200, status: 200, data: value });
let browser;
(async () => {
  browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--enable-webgl', '--ignore-gpu-blocklist'] });
  const errors = [];
  async function newPage(options = {}) {
    const context = await browser.newContext({ viewport: { width: 1672, height: 941 }, ...options });
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => {
      if (/GL_INVALID_|mergeGeometries\(\) failed|Shader Error/.test(message.text())) errors.push(message.text());
    });
    await page.route('**/api/v1/gallery', route => route.fulfill({ json: envelope(data) }));
    return page;
  }
  const layoutPage = await newPage({ reducedMotion: 'reduce' });
  await layoutPage.goto(base + '/gallery', { waitUntil: 'domcontentloaded' });
  await layoutPage.getByRole('button', { name: '开始参观', exact: true }).waitFor({ timeout: 30000 });
  await layoutPage.evaluate(() => document.fonts.ready);
  const layouts = [];
  await layoutPage.locator('.cabin-backdrop').evaluate(img => img.decode());
  for (const [width, height] of [[1920, 912], [1672, 941], [1440, 900], [1280, 720], [1024, 768], [768, 1024], [390, 844], [375, 667]]) {
    await layoutPage.setViewportSize({ width, height });
    const result = await layoutPage.evaluate(() => {
      const copy = document.querySelector('.entry-copy').getBoundingClientRect();
      const dock = document.querySelector('.exhibition-dock').getBoundingClientRect();
      const image = document.querySelector('.cabin-backdrop'), frame = image.getBoundingClientRect();
      const button = document.querySelector('.entry-copy .brass-button'), rect = button.getBoundingClientRect();
      return { viewport: [innerWidth, innerHeight], gap: dock.top - copy.bottom,
        visible: rect.bottom <= innerHeight && button.contains(document.elementFromPoint(rect.x + rect.width / 2, rect.bottom - 4)),
        imageUncropped: Math.abs(frame.width / frame.height - image.naturalWidth / image.naturalHeight) < .01 && getComputedStyle(image).objectFit === 'contain',
        imageSeparate: frame.left >= copy.right || frame.top >= copy.bottom,
        dockSeparate: dock.top >= frame.bottom,
        overflow: document.documentElement.scrollWidth > innerWidth };
    });
    assert(result.gap >= 16 && result.visible && !result.overflow, JSON.stringify(result));
    assert(result.imageUncropped && result.imageSeparate && result.dockSeparate, JSON.stringify(result));
    layouts.push(result);
    if ([1920, 1280, 390].includes(width)) await layoutPage.screenshot({ path: path.join(output, `entry-layout-${width}.png`), fullPage: true });
  }
  await layoutPage.context().close();
  const page = await newPage();
  await page.goto(base + '/gallery', { waitUntil: 'domcontentloaded' });
  await page.getByRole('button', { name: '开始参观', exact: true }).click({ timeout: 30000 });
  await page.waitForFunction(() => !!document.pointerLockElement);
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(output, 'tour.png') });
  const before = await page.locator('.gallery-minimap svg g').getAttribute('transform');
  await page.keyboard.down('w'); await page.waitForTimeout(400); await page.keyboard.up('w');
  assert.notEqual(await page.locator('.gallery-minimap svg g').getAttribute('transform'), before);
  await page.evaluate(() => document.dispatchEvent(new MouseEvent('mousemove', { movementY: 140 })));
  await page.keyboard.down('w');
  try { await page.locator('.gallery-active-prompt').filter({ hasText: '路飞的草帽' }).waitFor({ timeout: 8000 }); }
  finally { await page.keyboard.up('w'); }
  await page.keyboard.press('e');
  await page.locator('.gallery-artifact-dialog[open]').waitFor();
  assert.equal(await page.locator('#artifact-title').textContent(), '路飞的草帽');
  assert.equal(await page.locator('.pause-layer').count(), 0);
  await page.screenshot({ path: path.join(output, 'tour-artifact-detail.png') });
  await page.getByRole('button', { name: '关闭', exact: true }).click();
  await page.waitForFunction(() => !!document.pointerLockElement);
  // DOM 锁定标记先于 pointerlockchange 回调出现，等 HUD 恢复后再模拟下一次按键。
  await page.locator('.gallery-crosshair').waitFor();
  await page.keyboard.press('Escape');
  await page.waitForFunction(() => !document.pointerLockElement);
  await page.getByRole('button', { name: '返回序厅', exact: true }).click();
  await page.locator('.archive-rail button').nth(1).click();
  await page.getByRole('button', { name: '阅读本章' }).click();
  assert.equal(await page.locator('.chapter-essay h2').textContent(), '东海群像');
  await page.getByRole('button', { name: '查阅本章人物' }).click();
  assert.equal(await page.locator('.fallback-item').count(), 5);
  await page.getByRole('button', { name: '搜索人物档案', exact: true }).click();
  assert(await page.locator('.archive-search input').evaluate(e => e === document.activeElement));
  await page.locator('.archive-search input').fill('路飞');
  assert.equal(await page.locator('.fallback-item').count(), 1);
  await page.locator('.poster-button').first().click();
  await page.getByRole('button', { name: '下一份' }).click();
  assert.match(await page.locator('#character-title').textContent(), /索隆/);
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('dialog[open]').count(), 0);
  await page.locator('.archive-search input').fill('不存在的人物');
  assert.equal(await page.locator('.fallback-item').count(), 0);
  await page.getByRole('button', { name: '经典时刻', exact: true }).click();
  assert.equal(await page.locator('.moments-list article').count(), 9);
  await page.getByRole('button', { name: '人物档案', exact: true }).click();
  assert.equal(await page.locator('.artifact-catalog button').count(), 6);
  for (const name of ['路飞的草帽', '电话虫', '记录指针', '橡胶果实', '和道一文字', '黄金梅利号']) {
    await page.locator('.artifact-catalog button').filter({ hasText: name }).click();
    assert.equal(await page.locator('#artifact-title').textContent(), name);
    assert.equal(await page.locator('.artifact-features li').count(), 3);
    assert.equal(await page.locator('.gallery-artifact-dialog a').count(), 0);
    assert.equal(await page.locator('.artifact-model-credit').count(), 0);
    if (name === '电话虫') await page.screenshot({ path: path.join(output, 'artifact-detail.png') });
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('dialog[open]').count(), 0);
  }
  await page.goto(base + '/about', { waitUntil: 'domcontentloaded' });
  const cases = [];
  for (const count of [0, 1, 12, 40]) {
    if (count === 0) await page.route('**/one_piece_-going_merry.glb', route => route.abort());
    const result = await page.evaluate(async ({ count, data }) => {
      const { GalleryScene } = await import('/src/gallery/GalleryScene.ts');
      const { isWalkable } = await import('/src/gallery/layout.ts');
      const { artifacts, posterStartZ } = await import('/src/gallery/artifacts.ts');
      const THREE = await import('/node_modules/.vite/deps/three.js');
      const container = document.createElement('div');
      Object.assign(container.style, { position: 'fixed', inset: '0', zIndex: '99999' });
      document.body.append(container);
      const characters = Array.from({ length: count }, (_, i) => ({ ...data.characters[i % 9], id: i + 1, sort_order: i, poster_url: '/gallery/museum/portraits.webp?qa=' + i }));
      window.activeId = window.openedId = window.activeArtifactId = window.openedArtifactId = null;
      window.fixture = new GalleryScene(container, characters, false, {
        onActiveCharacter: c => { window.activeId = c?.id; }, onLockChange: () => {},
        onOpenCharacter: c => { window.openedId = c.id; }, onNavigation: () => {},
        onActiveArtifact: artifact => { window.activeArtifactId = artifact?.id; },
        onOpenArtifact: artifact => { window.openedArtifactId = artifact.id; },
        onUnavailable: reason => { throw new Error(reason); },
      });
      const fixture = window.fixture;
      await fixture.ready; await new Promise(r => setTimeout(r, 700));
      fixture.scene.updateMatrixWorld(true);
      const modelItems = artifacts.filter(item => item.id !== 'going-merry');
      const modelBoundsSafe = modelItems.every(item => {
        const model = fixture.scene.getObjectByName('artifact-model-' + item.id);
        if (!model) return false;
        const bounds = new THREE.Box3().setFromObject(model);
        return bounds.min.y >= (item.plinthHeight ?? 1.05) + .025 && bounds.max.y <= item.height &&
          bounds.min.x >= item.x - item.width/2 && bounds.max.x <= item.x + item.width/2 &&
          bounds.min.z >= item.z - item.depth/2 && bounds.max.z <= item.z + item.depth/2;
      });
      const room = fixture.scene.getObjectByName('CaptainsMuseum');
      const logo = fixture.scene.getObjectByName('MuseumLogo');
      const logoBounds = logo && new THREE.Box3().setFromObject(logo);
      const logoSafe = !!logoBounds && logoBounds.min.y > 2.8 && logoBounds.max.y < 4.3 &&
        logoBounds.max.z < -7 && !room.getObjectByName('MuseumLogoFallback');
      const ray = new THREE.Raycaster(), origin = new THREE.Vector3(), target = new THREE.Vector3();
      const postersClear = fixture.exhibits.every(exhibit => {
        const { x, z } = exhibit.group.position;
        origin.set(0, 1.7, z);
        return [-.7, 0, .7].every(dz => [1.6, 2.7, 3.8].every(y => {
          target.set(x, y, z + dz); const distance = origin.distanceTo(target);
          ray.set(origin, target.sub(origin).normalize()); ray.far = distance - .2;
          return ray.intersectObject(room, true).length === 0;
        }));
      });
      // 检查最终后处理输出，防止缺少 RenderPass 导致纯色空白。
      fixture.composer.render();
      const gl = fixture.renderer.getContext();
      const pixels = new Uint8Array(gl.drawingBufferWidth * gl.drawingBufferHeight * 4);
      gl.readPixels(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
      const colors = new Set();
      for (let i = 0; i < pixels.length; i += 4096) colors.add(`${pixels[i]},${pixels[i + 1]},${pixels[i + 2]}`);
      return { count, exhibits: fixture.exhibits.length, colors: colors.size, posters: fixture.posterCache.size,
        boundaries: !isWalkable(5, 0, fixture.hall) && !isWalkable(0, fixture.hall.minZ - 1, fixture.hall) && !isWalkable(0, fixture.hall.maxZ + 1, fixture.hall),
        artifactNodes: artifacts.filter(item => room.getObjectByName('artifact-' + item.id)).length,
        loadedModels: modelItems.filter(item => fixture.scene.getObjectByName('artifact-model-' + item.id)).length,
        fallbackReplaced: modelItems.every(item => !fixture.scene.getObjectByName('artifact-fallback-' + item.id)),
        modelBoundsSafe, logoSafe,
        shipFallback: !!fixture.scene.getObjectByName('DisplayShipFallback')?.children.length,
        artifacts: artifacts.every(item => !isWalkable(item.x, item.z, fixture.hall)),
        aisles: [-1.6, 1.6].every(x => Array.from({ length: Math.floor((fixture.hall.maxZ + 6) / .25) }, (_, i) => -6.8 + i * .25).every(z => isWalkable(x, z, fixture.hall))),
        postersClear, separated: artifacts.every(item => item.z + item.depth / 2 < posterStartZ - 1.4),
        entry: isWalkable(0, 5.8, fixture.hall) };
    }, { count, data });
    assert.equal(result.exhibits, count); assert(result.colors > 20, '漫游输出必须包含实际场景');
    assert(result.boundaries && result.artifacts && result.aisles && result.entry, JSON.stringify(result));
    assert.equal(result.artifactNodes, 6); assert(result.postersClear && result.separated); assert(result.posters <= 12);
    assert.equal(result.loadedModels, 5); assert(result.fallbackReplaced && result.modelBoundsSafe, JSON.stringify(result));
    assert(result.logoSafe, '立体徽标必须位于前舱背墙且替换文字备用铭牌');
    if (count === 1) {
      await page.waitForFunction(() => !!window.fixture.scene.getObjectByName('DisplayShip'), { timeout: 30000 });
      const rotation = await page.evaluate(async () => {
        const s = window.fixture;
        const THREE = await import('/node_modules/.vite/deps/three.js');
        const { artifacts } = await import('/src/gallery/artifacts.ts');
        const ids = ['gum-gum', 'going-merry'];
        const pivots = ids.map(id => s.scene.getObjectByName('rotating-display-' + id));
        const angles = () => pivots.map(p => p.rotation.y);
        const wait = () => new Promise(resolve => setTimeout(resolve, 180));
        s.camera.position.set(0, 1.7, 2.8); s.camera.lookAt(0, 1.7, -3);
        s.setRunning(true); s.controls.isLocked = true;
        const before = angles(); await wait(); const after = angles();
        s.setRunning(false); await wait(); const paused = angles();
        s.reducedMotion = true; s.setRunning(true); s.controls.isLocked = true;
        await wait(); const reduced = angles();
        s.reducedMotion = false;
        s.camera.lookAt(0, 1.7, 12); await wait(); const offscreen = angles();
        s.setRunning(false);
        // 全周采样真实顶点边界，确认船尾/船首不会扫出展台进入通道。
        const contained = pivots.every((pivot, index) => {
          const item = artifacts.find(item => item.id === ids[index]);
          for (let step = 0; step < 24; step++) {
            pivot.rotation.y = step * Math.PI / 12;
            const box = new THREE.Box3().setFromObject(pivot, true);
            if (box.min.x < item.x - item.width / 2 || box.max.x > item.x + item.width / 2 ||
                box.min.z < item.z - item.depth / 2 || box.max.z > item.z + item.depth / 2) return false;
          }
          pivot.rotation.y = 0;
          return true;
        });
        s.camera.lookAt(0, 1.7, -3); s.setRunning(true);
        return { moving: after.every((angle, i) => angle > before[i]),
          paused: paused.every((angle, i) => angle === after[i]),
          reduced: reduced.every((angle, i) => angle === paused[i]),
          offscreen: offscreen.every((angle, i) => angle === reduced[i]), contained };
      });
      assert(Object.values(rotation).every(Boolean), JSON.stringify(rotation));
      result.rotation = rotation;
    }
    if (count === 0) {
      assert(result.shipFallback, '船模加载失败时必须保留备用船模');
      const artifactIds = await page.evaluate(async () => (await import('/src/gallery/artifacts.ts')).artifacts.map(item => item.id));
      for (const id of artifactIds) {
        await page.evaluate(async id => {
          const item = (await import('/src/gallery/artifacts.ts')).artifacts.find(item => item.id === id);
          const s = window.fixture;
          // 从展台右侧通道正对展签，避免相邻左舷展台落在射线起点内。
          s.camera.position.set(item.x + item.width / 2 + 1, 1.7, item.z);
          // 直接看向展签也应可交互，防止只允许命中道具上半部。
          s.camera.lookAt(item.x, .69, item.z);
          s.camera.updateMatrixWorld(); s.controls.isLocked = true; s.interaction();
        }, id);
        assert.equal(await page.evaluate(() => window.activeArtifactId), id);
        await page.keyboard.press('e');
        assert.equal(await page.evaluate(() => window.openedArtifactId), id);
        await page.evaluate(async id => {
          const item = (await import('/src/gallery/artifacts.ts')).artifacts.find(item => item.id === id);
          const s = window.fixture; s.controls.isLocked = false;
          s.camera.position.set(item.x + .45, 2.05, item.z + 2.5); s.camera.lookAt(item.x, 1.55, item.z);
          s.setRunning(true);
        }, id);
        await page.waitForTimeout(100);
        await page.screenshot({ path: path.join(output, id + '.png') });
      }
    }
    if (count) {
      await page.evaluate(() => {
        // 旋转测试曾模拟 isLocked；真实点击前清除，防止鼠标移到按钮时意外转动镜头。
        window.fixture.controls.isLocked = false;
        const first = window.fixture.exhibits[0].group.position;
        window.fixture.camera.position.set(-2, 1.7, first.z); window.fixture.camera.lookAt(first);
        const button = document.createElement('button'); button.id = 'fixture-lock'; button.textContent = 'Lock';
        Object.assign(button.style, { position: 'fixed', top: '0', left: '0', zIndex: '100000' });
        button.onclick = () => window.fixture.lock(); document.body.append(button);
      });
      await page.locator('#fixture-lock').click(); await page.waitForFunction(() => window.activeId === 1);
      if (count === 12) {
        // 缓存测试使用图集作为远程图；截图改用馆内真实的单人后备画像。
        await page.evaluate(() => {
          const s = window.fixture;
          const first = s.exhibits[0].group.position;
          s.camera.position.set(0, 1.7, first.z); s.camera.lookAt(first);
          s.updatePosters();
          for (const exhibit of s.exhibits) exhibit.poster.map = exhibit.fallback;
        });
        await page.waitForTimeout(100);
        await page.screenshot({ path: path.join(output, 'poster-clear.png') });
      }
      await page.keyboard.press('e'); assert.equal(await page.evaluate(() => window.openedId), 1);
      await page.keyboard.press('Escape'); await page.locator('#fixture-lock').evaluate(e => e.remove());
    }
    if (count === 40) {
      await page.evaluate(() => { window.fixture.camera.position.z = window.fixture.hall.maxZ - 2; window.fixture.setRunning(true); });
      await page.waitForFunction(() => window.fixture.exhibits.at(-1).poster.map !== window.fixture.exhibits.at(-1).fallback);
      const cache = await page.evaluate(() => ({ size: window.fixture.posterCache.size, evicted: window.fixture.exhibits[0].poster.map === window.fixture.exhibits[0].fallback }));
      assert(cache.size <= 12 && cache.evicted); result.cache = cache;
    }
    assert.deepEqual(await page.evaluate(() => {
      const fixture = window.fixture; fixture.dispose(); fixture.container.remove();
      return [fixture.textures.size, fixture.materials.size, fixture.geometries.size, document.querySelectorAll('.gallery-canvas').length];
    }), [0, 0, 0, 0]);
    if (count === 0) await page.unroute('**/one_piece_-going_merry.glb');
    cases.push(result);
  }
  // 单件模型损坏必须保留对应展品，其他四件仍正常加载且不影响参观。
  await page.route('**/gallery/artifacts/den-den-mushi.glb', route => route.abort());
  await page.route('**/gallery/artifacts/one-piece-logo.glb', route => route.abort());
  const modelRecovery = await page.evaluate(async () => {
    const { GalleryScene } = await import('/src/gallery/GalleryScene.ts');
    const container = document.createElement('div');
    Object.assign(container.style, { position: 'fixed', inset: '0' }); document.body.append(container);
    const scene = new GalleryScene(container, [], true, { onActiveCharacter() {}, onLockChange() {}, onOpenCharacter() {}, onNavigation() {}, onUnavailable(reason) { throw Error(reason); } });
    await scene.ready;
    const fallback = scene.scene.getObjectByName('artifact-fallback-den-den-mushi');
    const result = !!fallback?.children.length && !!scene.scene.getObjectByName('MuseumLogoFallback') &&
      !scene.scene.getObjectByName('MuseumLogo') && !scene.scene.getObjectByName('artifact-model-den-den-mushi') &&
      ['straw-hat', 'log-pose', 'gum-gum', 'wado'].every(id => !!scene.scene.getObjectByName('artifact-model-' + id));
    scene.dispose(); container.remove(); return result;
  });
  assert(modelRecovery); await page.unroute('**/gallery/artifacts/den-den-mushi.glb');
  await page.unroute('**/gallery/artifacts/one-piece-logo.glb');
  const phone = await newPage({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  await phone.goto(base + '/gallery', { waitUntil: 'domcontentloaded' }); await phone.getByRole('button', { name: '开始参观', exact: true }).click();
  assert.equal(await phone.locator('.gallery-canvas').count(), 0); assert.equal(await phone.locator('.fallback-item').count(), 9);
  assert(await phone.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  await phone.locator('.poster-button').first().click(); await phone.getByRole('button', { name: '下一份' }).click();
  assert.match(await phone.locator('#character-title').textContent(), /索隆/);
  await phone.getByRole('button', { name: '关闭', exact: true }).click();
  await phone.locator('.artifact-catalog button').filter({ hasText: '路飞的草帽' }).click();
  assert.equal(await phone.locator('#artifact-title').textContent(), '路飞的草帽');
  assert.equal(await phone.locator('.gallery-artifact-dialog a, .artifact-model-credit').count(), 0);
  assert(await phone.locator('.gallery-artifact-dialog').evaluate(e => e.scrollWidth <= e.clientWidth));
  await phone.screenshot({ path: path.join(output, 'mobile-artifact.png') });
  await phone.getByRole('button', { name: '关闭', exact: true }).click(); await phone.context().close();
  const fallbacks = [];
  for (const mode of ['webgl', 'pointer', 'model', 'api', 'empty', 'broken-poster']) {
    const tab = await newPage({ viewport: { width: 1280, height: 720 } });
    if (mode === 'webgl') await tab.addInitScript(() => {
      const original = HTMLCanvasElement.prototype.getContext;
      HTMLCanvasElement.prototype.getContext = function(type, ...args) { return type === 'webgl2' ? null : original.call(this, type, ...args); };
    });
    if (mode === 'pointer') await tab.addInitScript(() => {
      Element.prototype.requestPointerLock = () => { document.dispatchEvent(new Event('pointerlockerror')); return Promise.reject(new Error('test denial')); };
    });
    if (mode === 'model') await tab.route('**/one_piece_-going_merry.glb', route => route.abort());
    if (mode === 'api') await tab.route('**/api/v1/gallery', route => route.fulfill({ status: 503, body: 'unavailable' }));
    if (mode === 'empty' || mode === 'broken-poster') await tab.route('**/api/v1/gallery', route => route.fulfill({ json: envelope({ ...data, characters: mode === 'empty' ? [] : [{ ...data.characters[0], poster_url: '/uploads/gallery-qa-missing.png' }] }) }));
    await tab.goto(base + '/gallery', { waitUntil: 'domcontentloaded' });
    if (mode === 'api') {
      await tab.getByRole('button', { name: '重新读取' }).waitFor(); await tab.unroute('**/api/v1/gallery');
      await tab.route('**/api/v1/gallery', route => route.fulfill({ json: envelope(data) }));
      await tab.getByRole('button', { name: '重新读取' }).click(); await tab.getByRole('button', { name: '开始参观', exact: true }).waitFor();
    } else if (mode === 'broken-poster') {
      await tab.getByRole('button', { name: '人物档案', exact: true }).click(); await tab.locator('.poster-button').first().click();
      await tab.waitForFunction(() => !document.querySelector('.dialog-poster img'));
      assert(await tab.locator('.dialog-poster .portrait-painting').isVisible());
    } else {
      await tab.getByRole('button', { name: '开始参观', exact: true }).click();
      if (mode === 'webgl' || mode === 'pointer') await tab.locator('.gallery-fallback').waitFor();
      else await tab.waitForFunction(() => !!document.pointerLockElement);
    }
    fallbacks.push(mode); await tab.context().close();
  }
  assert.deepEqual(errors, []);
  const report = { layouts, cases, fallbacks, errors, mobile: true, search: true, chapters: true, details: true, artifacts: true, modelRecovery, pointerLock: true };
  fs.writeFileSync(path.join(output, 'browser-report.json'), JSON.stringify(report, null, 2)); console.log(JSON.stringify(report, null, 2));
})().catch(async error => {
  console.error(error); process.exitCode = 1;
  const pages = browser?.contexts().flatMap(context => context.pages()) ?? [];
  for (const [index, page] of pages.entries()) {
    await page.screenshot({ path: path.join(output, `failure-${index}.png`) }).catch(() => {});
    console.error(await page.evaluate(() => ({ url: location.href, locked: !!document.pointerLockElement, dialogs: document.querySelectorAll('dialog[open]').length, text: document.body.innerText.slice(-1800) })).catch(() => ({})));
  }
}).finally(async () => { await browser?.close(); });

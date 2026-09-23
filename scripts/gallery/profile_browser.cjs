// 固定路线和视口对比漫游性能；结果仅代表当前机器/浏览器。
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const output = process.env.GALLERY_QA_OUTPUT || path.join(os.tmpdir(), 'gallery-museum-qa');
const label = process.env.GALLERY_PROFILE_LABEL || 'profile';
fs.mkdirSync(output, { recursive: true });
(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1920, height: 912 }, deviceScaleFactor: 1 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => {
      if (/GL_INVALID_|mergeGeometries\(\) failed|Shader Error/.test(message.text())) errors.push(message.text());
    });
    await page.goto((process.env.GALLERY_URL || 'http://127.0.0.1:5173') + '/about', { waitUntil: 'domcontentloaded' });
    await page.evaluate(async () => {
      const { GalleryScene } = await import('/src/gallery/GalleryScene.ts');
      const container = document.createElement('div');
      Object.assign(container.style, { position: 'fixed', inset: 0, zIndex: 99999 }); document.body.append(container);
      const names = ['路飞','索隆','娜美','乌索普','山治','乔巴','罗宾','弗兰奇','甚平'];
      const characters = Array.from({ length: 15 }, (_, i) => ({ id: i + 1, name: names[i % names.length], epithet: '航海者', faction: '草帽一伙', bounty: '', ability: '', description: '', quote: '', poster_url: null, is_visible: true, sort_order: i }));
      window.profileScene = new GalleryScene(container, characters, false, { onActiveCharacter() {}, onLockChange() {}, onOpenCharacter() {}, onNavigation() {}, onUnavailable(reason) { throw Error(reason); } });
      await window.profileScene.ready;
    });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: path.join(output, label + '-scene.png') });
    const report = await page.evaluate(async () => {
      const s = window.profileScene, timings = {}, originals = {}, frameTimes = [], draws = [];
      for (const name of ['move','interaction','navigation']) {
        originals[name] = s[name]; timings[name] = [];
        s[name] = function(...args) { const t = performance.now(); const result = originals[name].apply(this,args); timings[name].push(performance.now()-t); return result; };
      }
      const renderer = s.renderer, originalRender = s.composer.render.bind(s.composer);
      timings.render = []; renderer.info.autoReset = false;
      s.composer.render = (...args) => { renderer.info.reset(); const t = performance.now(); originalRender(...args); timings.render.push(performance.now()-t); draws.push(renderer.info.render.calls); };
      s.controls.isLocked = true;
      let last = performance.now(); const started = last;
      while (performance.now() - started < 8000) await new Promise(resolve => requestAnimationFrame(now => {
        frameTimes.push(now-last); last=now;
        const phase = (now-started)/8000;
        s.camera.position.set(Math.sin(phase*Math.PI*2)*1.5,1.7,5.8+Math.sin(phase*Math.PI)*5);
        s.camera.lookAt(Math.sin(phase*Math.PI*2)*3,2,-4);
        resolve();
      }));
      const summary = values => { values.sort((a,b)=>a-b); return { average: +(values.reduce((a,b)=>a+b,0)/values.length).toFixed(2), p95: +values[Math.floor(values.length*.95)].toFixed(2) }; };
      const frame = summary(frameTimes), gl = renderer.getContext(), ext=gl.getExtension('WEBGL_debug_renderer_info');
      let triangles=0; s.scene.traverse(o=>{if(o.isMesh)triangles+=(o.geometry.index?.count??o.geometry.attributes.position.count)/3;});
      s.controls.isLocked=false;
      s.camera.position.set(-.35,1.7,2.8); s.camera.lookAt(0,2.05,-5);
      return { viewport:[innerWidth,innerHeight], renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):'unknown', fps:+(1000/frame.average).toFixed(1), frameMs:frame, cpuMs:Object.fromEntries(Object.entries(timings).map(([k,v])=>[k,summary(v)])), drawCalls:summary(draws), triangles, pixelRatio:renderer.getPixelRatio() };
    });
    await page.waitForTimeout(100);
    await page.screenshot({ path: path.join(output, label + '-scene.png') });
    report.errors = [...new Set(errors)];
    fs.writeFileSync(path.join(output,label+'.json'),JSON.stringify(report,null,2)); console.log(JSON.stringify(report,null,2));
    if (errors.length) throw new Error('渲染错误，性能数据不可用');
    await page.evaluate(()=>window.profileScene.dispose());
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});

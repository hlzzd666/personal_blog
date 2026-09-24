const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ts = require("typescript");

const { outputText } = ts.transpileModule(
  fs.readFileSync(path.join(__dirname, "../web/src/composables/useAboutMotion.ts"), "utf8"),
  { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } },
);

function harness({ supported = true } = {}) {
  const ticks = [], observers = [], frames = new Map(), listeners = new Map();
  let unmount, changed, frameId = 0;
  function element(attributes, top, height) {
    const classes = new Set(), styles = new Map();
    return {
      top, height, reads: 0, classes, styles,
      classList: {
        add: (value) => classes.add(value),
        remove: (value) => classes.delete(value),
        contains: (value) => classes.has(value),
      },
      style: { setProperty: (key, value) => styles.set(key, value) },
      hasAttribute: (value) => attributes.includes(value),
      getBoundingClientRect() { this.reads++; return { top: this.top, height: this.height }; },
    };
  }
  const scene = element(["data-about-scene"], 800, 200);
  const offscreen = element(["data-about-scene"], 2000, 500);
  const reveal = element(["data-about-reveal"], 900, 50);
  const root = element([], 0, 4000);
  root.querySelectorAll = (selector) => selector === "[data-about-scene]" ? [scene, offscreen] : [reveal];
  const enabled = { value: true }, pageRoot = { value: root };
  class Observer {
    constructor(callback) { this.callback = callback; this.targets = new Set(); observers.push(this); }
    observe(target) { this.targets.add(target); }
    unobserve(target) { this.targets.delete(target); }
    disconnect() { this.disconnected = true; this.targets.clear(); }
  }
  const exports = {};
  vm.runInNewContext(outputText, {
    exports,
    require(name) {
      assert.equal(name, "vue");
      return {
        nextTick: () => new Promise((resolve) => ticks.push(resolve)),
        onBeforeUnmount: (callback) => { unmount = callback; },
        watch: (_, callback) => { changed = callback; callback(); },
      };
    },
    IntersectionObserver: supported ? Observer : undefined,
    window: {
      innerHeight: 1000,
      requestAnimationFrame: (callback) => { frames.set(++frameId, callback); return frameId; },
      cancelAnimationFrame: (id) => frames.delete(id),
      addEventListener: (name, callback, options) => { assert.equal(options.passive, true); listeners.set(name, callback); },
      removeEventListener: (name) => listeners.delete(name),
    },
  });
  return {
    ...exports.useAboutMotion(pageRoot, enabled),
    root, scene, offscreen, reveal, enabled, observers, frames, listeners,
    changed: () => changed(), unmount: () => unmount(),
    async tick() { ticks.splice(0).forEach((resolve) => resolve()); await new Promise(setImmediate); },
    frame() { const pending = [...frames.values()]; frames.clear(); pending.forEach((callback) => callback()); },
  };
}

async function check() {
  const active = harness();
  await active.tick();
  assert.equal(active.root.classes.has("motion-ready"), true);
  const first = active.observers[0];
  first.callback([
    { target: active.scene, isIntersecting: true },
    { target: active.reveal, isIntersecting: true },
  ]);
  active.listeners.get("scroll")();
  active.listeners.get("resize")();
  assert.equal(active.frames.size, 1, "同一帧合并滚动、尺寸和观察器回调");
  active.frame();
  assert.equal(active.scene.styles.get("--scene-progress"), "0.0000", "视口 80% 为场景起点");
  assert.equal(active.offscreen.reads, 0, "离屏场景不读取布局");
  assert.equal(active.reveal.classes.has("is-revealed"), true);
  assert.equal(first.targets.has(active.reveal), false, "内容只显现一次");
  active.scene.top = 400;
  active.root.top = -1500;
  active.listeners.get("scroll")(); active.frame();
  assert.equal(active.scene.styles.get("--scene-progress"), "0.5000");
  assert.equal(active.scene.styles.get("--scene-travel"), "0.0000");
  assert.equal(active.root.styles.get("--reading-progress"), "0.5000");
  active.scene.top = -10;
  active.listeners.get("scroll")(); active.frame();
  assert.equal(active.scene.styles.get("--scene-progress"), "1.0000", "场景底缘到 20% 时结束并钳制");

  const older = active.refresh(), newer = active.refresh();
  await active.tick(); await Promise.all([older, newer]);
  assert.equal(active.observers.length, 2, "重叠 refresh 只创建最新观察器");
  active.frame();
  first.callback([{ target: active.offscreen, isIntersecting: true }]);
  assert.equal(active.frames.size, 0, "失效观察器不能排入动画帧");
  active.enabled.value = false; active.changed(); await active.tick();
  assert.equal(active.listeners.size, 0);
  assert.equal(active.frames.size, 0);
  assert.equal(active.root.classes.has("motion-ready"), false);
  assert.equal(active.scene.styles.get("--scene-travel"), "0");
  assert.equal(active.offscreen.styles.get("--scene-progress"), "0.5");
  assert.equal(active.reveal.classes.has("is-revealed"), true);

  const disposed = harness();
  disposed.unmount(); await disposed.tick();
  assert.equal(disposed.observers.length, 0, "卸载后异步 refresh 不访问 DOM");
  const fallback = harness({ supported: false });
  await fallback.tick();
  assert.equal(fallback.reveal.classes.has("is-revealed"), true, "不支持观察器时内容可读");
  assert.equal(fallback.listeners.size, 0);
  console.log("PASS: about motion 进度、可见场景、单帧合并、显现、禁用与生命周期竞态");
}

check().catch((error) => { console.error(error); process.exitCode = 1; });

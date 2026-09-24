const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ts = require("typescript");

// 运行实际 composable，只替换 Vue 生命周期和浏览器边界，精确控制 nextTick 时序。
const source = fs.readFileSync(
  path.join(__dirname, "../web/src/composables/useViewportReveal.ts"),
  "utf8",
);
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
});

function createHarness({ reducedMotion = false } = {}) {
  const ticks = [];
  const observers = [];
  const revealed = new Set();
  const element = {
    classList: { add: (name) => revealed.add(name) },
    style: { setProperty() {} },
  };
  const root = { querySelectorAll: () => [element] };
  let unmount;
  class Observer {
    constructor(callback) {
      this.callback = callback;
      this.targets = new Set();
      this.disconnected = false;
      observers.push(this);
    }
    observe(target) { this.targets.add(target); }
    unobserve(target) { this.targets.delete(target); }
    disconnect() { this.disconnected = true; this.targets.clear(); }
  }
  const moduleExports = {};
  vm.runInNewContext(outputText, {
    exports: moduleExports,
    require(name) {
      assert.equal(name, "vue");
      return {
        nextTick: () => new Promise((resolve) => ticks.push(resolve)),
        onBeforeUnmount: (callback) => { unmount = callback; },
      };
    },
    document: root,
    window: { matchMedia: () => ({ matches: reducedMotion }) },
    IntersectionObserver: Observer,
  });
  const { observe } = moduleExports.useViewportReveal();
  return {
    observe: () => observe(root),
    flushTicks: () => ticks.splice(0).forEach((resolve) => resolve()),
    unmount: () => unmount(),
    observers,
    revealed,
    element,
  };
}

async function check() {
  const disposed = createHarness();
  const pending = disposed.observe();
  disposed.unmount();
  disposed.flushTicks();
  await pending;
  await disposed.observe();
  assert.equal(disposed.observers.length, 0, "卸载后不得创建或观察 DOM");

  const normal = createHarness();
  const first = normal.observe();
  normal.flushTicks();
  await first;
  assert.equal(normal.observers[0].targets.has(normal.element), true);
  const second = normal.observe();
  assert.equal(normal.observers[0].disconnected, true, "重新观察先断开旧实例");
  normal.observers[0].callback([{ isIntersecting: true, target: normal.element }]);
  assert.equal(normal.revealed.size, 0, "旧观察器的已排队回调不得修改 DOM");
  normal.flushTicks();
  await second;
  assert.equal(normal.observers.length, 2);
  normal.observers[1].callback([{ isIntersecting: true, target: normal.element }]);
  assert.equal(normal.revealed.has("is-revealed"), true, "正常进入视口仍显示内容");
  assert.equal(normal.observers[1].targets.size, 0, "显现后停止观察该元素");
  normal.unmount();
  assert.equal(normal.observers[1].disconnected, true);

  const overlapping = createHarness();
  const older = overlapping.observe();
  const newer = overlapping.observe();
  overlapping.flushTicks();
  await Promise.all([older, newer]);
  assert.equal(overlapping.observers.length, 1, "重叠请求只保留最新观察器");

  const reduced = createHarness({ reducedMotion: true });
  const immediate = reduced.observe();
  reduced.flushTicks();
  await immediate;
  assert.equal(reduced.revealed.has("is-revealed"), true, "减弱动效时直接显示内容");
  assert.equal(reduced.observers.length, 0, "减弱动效时不创建观察器");
  console.log("PASS: viewport reveal 生命周期、重复观察、异步竞态和减弱动效");
}

check().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

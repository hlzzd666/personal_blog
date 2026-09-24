import { nextTick, onBeforeUnmount, watch, type Ref } from "vue";

const clamp = (value: number) => Math.min(1, Math.max(0, value));

export function useAboutMotion(pageRoot: Ref<HTMLElement | null>, enabled: Readonly<Ref<boolean>>) {
  let observer: IntersectionObserver | undefined;
  let root: HTMLElement | null = null;
  let frame = 0;
  let generation = 0;
  let disposed = false;
  const visibleScenes = new Set<HTMLElement>();

  function render() {
    frame = 0;
    if (!root || disposed || !enabled.value) return;
    const height = window.innerHeight;
    const page = root.getBoundingClientRect();
    // 先统一读取布局，再写 CSS 变量，避免滚动中交错触发布局计算。
    const scenes = Array.from(visibleScenes, (element) => {
      const rect = element.getBoundingClientRect();
      return {
        element,
        progress: clamp((height * 0.8 - rect.top) / (rect.height + height * 0.6)),
      };
    });
    const reading = clamp(-page.top / Math.max(1, page.height - height));
    root.style.setProperty("--reading-progress", reading.toFixed(4));
    scenes.forEach(({ element, progress }) => {
      element.style.setProperty("--scene-progress", progress.toFixed(4));
      element.style.setProperty("--scene-travel", (progress * 2 - 1).toFixed(4));
    });
  }

  function schedule() {
    if (!frame && root && !disposed && enabled.value) {
      frame = window.requestAnimationFrame(render);
    }
  }

  function disconnect() {
    observer?.disconnect();
    observer = undefined;
    visibleScenes.clear();
    window.cancelAnimationFrame(frame);
    frame = 0;
    window.removeEventListener("scroll", schedule);
    window.removeEventListener("resize", schedule);
    root?.classList.remove("motion-ready");
  }

  async function refresh() {
    if (disposed) return;
    const currentGeneration = ++generation;
    disconnect();
    await nextTick();
    if (disposed || currentGeneration !== generation) return;
    root = pageRoot.value;
    if (!root) return;
    const scenes = Array.from(root.querySelectorAll<HTMLElement>("[data-about-scene]"));
    const reveals = Array.from(root.querySelectorAll<HTMLElement>("[data-about-reveal]"));

    if (!enabled.value || typeof IntersectionObserver === "undefined") {
      reveals.forEach((element) => element.classList.add("is-revealed"));
      scenes.forEach((element) => {
        element.style.setProperty("--scene-progress", "0.5");
        element.style.setProperty("--scene-travel", "0");
      });
      root.style.setProperty("--reading-progress", "0");
      return;
    }

    const sceneSet = new Set(scenes);
    observer = new IntersectionObserver((entries) => {
      if (disposed || currentGeneration !== generation || !enabled.value) return;
      entries.forEach((entry) => {
        const element = entry.target as HTMLElement;
        if (sceneSet.has(element)) {
          if (entry.isIntersecting) visibleScenes.add(element);
          else visibleScenes.delete(element);
        }
        if (entry.isIntersecting && element.hasAttribute("data-about-reveal")) {
          element.classList.add("is-revealed");
          if (!sceneSet.has(element)) observer?.unobserve(element);
        }
      });
      schedule();
    });
    scenes.forEach((element) => observer?.observe(element));
    reveals.forEach((element) => {
      if (!element.classList.contains("is-revealed")) observer?.observe(element);
    });
    root.classList.add("motion-ready");
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule, { passive: true });
    schedule();
  }

  watch([pageRoot, enabled], () => void refresh(), { flush: "post", immediate: true });
  onBeforeUnmount(() => {
    disposed = true;
    generation += 1;
    disconnect();
    root = null;
  });

  return { refresh };
}

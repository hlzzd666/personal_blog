export const museumAsset = (name: string) => `${import.meta.env.BASE_URL}gallery/museum/${name}`;
export const entryChapter = { id: 0, artwork_index: 0, title: "序厅", subtitle: "从这里，开启伟大航路的旅程。", heading: "伟大航路\n人物档案馆", description: "他们曾在这片大海上相遇、战斗、梦想——\n这些名字，构成了一个时代的航海史。", note: "走进他们的故事，重返伟大航路。", label: "ONE PIECE CHARACTER ARCHIVE", story: "一顶草帽、一艘船、一个尚未完成的约定。从东海到新世界，航路把各自孤独的梦想连在了一起。沿着馆中的人物画像，重访那些决定启航的瞬间。" };

const portraitNames = ["路飞", "索隆", "娜美", "乌索普", "山治", "乔巴", "罗宾", "弗兰奇", "甚平"];
export function portraitIndex(name: string) {
  return portraitNames.findIndex((part) => name.includes(part));
}
// 原画为非等高三行，使用实测分界避免相邻人物露出在画框内。
export function portraitRegion(index: number) {
  const starts = [0, 477, 960], heights = [477, 483, 576];
  const row = Math.floor(index / 3);
  return { x: (index % 3) / 3, y: starts[row]! / 1536, width: 1 / 3, height: heights[row]! / 1536 };
}
export function portraitStyle(name: string) {
  const index = portraitIndex(name);
  const region = index < 0 ? null : portraitRegion(index);
  return index < 0 ? undefined : {
    backgroundImage: `url(${museumAsset("portraits.webp")})`,
    backgroundSize: `300% ${100 / region!.height}%`,
    backgroundPosition: `${(index % 3) * 50}% ${region!.y / (1 - region!.height) * 100}%`,
  };
}

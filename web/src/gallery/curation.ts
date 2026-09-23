import type { GalleryCharacter } from "../api/gallery";

export const museumAsset = (name: string) => `${import.meta.env.BASE_URL}gallery/museum/${name}`;
export const chapters = [
  { title: "序厅", subtitle: "从这里，开启伟大航路的旅程。", heading: "伟大航路\n人物档案馆", description: "他们曾在这片大海上相遇、战斗、梦想——\n这些名字，构成了一个时代的航海史。", note: "走进他们的故事，重返伟大航路。", label: "ONE PIECE CHARACTER ARCHIVE", story: "一顶草帽、一艘船、一个尚未完成的约定。从东海到新世界，航路把各自孤独的梦想连在了一起。沿着馆中的人物画像，重访那些决定启航的瞬间。" },
  { title: "东海群像", subtitle: "每一段传奇，都始于一次启航。", heading: "梦想的起点\n东海群像", description: "小小的港口，装得下最辽阔的梦想。\n在成为同伴以前，他们先选择了自己的航向。", note: "从风车村出发，读懂最初的约定。", label: "CHAPTER II · EAST BLUE", story: "路飞向大海许下成为海贼王的愿望；索隆守住与挚友的约定；娜美想画出世界的海图；乌索普追逐勇敢；山治寻找传说中的 All Blue。东海篇把五个梦想写进同一段航程。" },
  { title: "伟大航路", subtitle: "以相遇为坐标，以信念为方向。", heading: "相遇与远方\n伟大航路", description: "航路并不承诺答案，只不断带来新的相遇。\n有人寻找历史，有人寻找一处可以归来的地方。", note: "循着记录指针，翻开下一段航海志。", label: "CHAPTER III · GRAND LINE", story: "越过颠倒山，气候、岛屿和规则都变得陌生。乔巴把医者的心带上船；罗宾继续追寻历史；弗兰奇把造船的梦想交付大海。伙伴的意义，在一次次选择中变得具体。" },
  { title: "新世界", subtitle: "穿过风暴，抵达自己的答案。", heading: "时代的回声\n新世界", description: "当航程驶入风暴深处，梦想仍然指向远方。\n那些被守护的约定，成为继续前行的力量。", note: "越过地平线，重访仍在继续的故事。", label: "CHAPTER IV · NEW WORLD", story: "新世界让每一个选择都承担更大的重量。甚平带着对同伴的承诺走上甲板，旧时代的意志与新的航程在这里交汇。展览停在此刻，属于他们的故事仍在继续。" },
] as const;

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
export function chapterCharacters(characters: GalleryCharacter[], chapter: number) {
  if (chapter === 0) return characters;
  const names = chapter === 1 ? portraitNames.slice(0, 5) : chapter === 2 ? portraitNames.slice(5, 8) : portraitNames.slice(8);
  return characters.filter((character) => names.some((name) => character.name.includes(name)));
}

import dimensions from "./layout.json";
import { artifacts, posterStartZ } from "./artifacts";

export { dimensions };
export function createLayout(count: number) {
  const bays = Math.max(
    dimensions.minimumBays,
    Math.ceil(Math.min(count, dimensions.maximumCharacters) / 2),
  );
  const cabinBack = posterStartZ + (bays - 1) * dimensions.bayLength + 2;
  const cabinFront = -8;
  return {
    bays,
    cabinBack,
    cabinFront,
    minZ: cabinFront,
    maxZ: cabinBack,
  };
}
export type HallLayout = ReturnType<typeof createLayout>;

export function exhibitPosition(index: number) {
  const side = index % 2 === 0 ? -1 : 1;
  return { x: side * dimensions.frameX, z: posterStartZ + Math.floor(index / 2) * dimensions.bayLength, side };
}

export function isWalkable(x: number, z: number, hall: HallLayout) {
  const radius = dimensions.playerRadius;
  if (z < hall.minZ + 0.6 || z > hall.maxZ - 0.6) return false;
  if (Math.abs(x) > 4.25 - radius) return false;
  // 与展台共用尺寸，画像长廊内不设置家具碰撞体。
  if (artifacts.some(item =>
    Math.abs(x - item.x) < item.width / 2 + radius && Math.abs(z - item.z) < item.depth / 2 + radius,
  )) return false;
  return true;
}

import dimensions from "./layout.json";

export { dimensions };
export function createLayout(count: number) {
  const bays = Math.max(
    dimensions.minimumBays,
    Math.ceil(Math.min(count, dimensions.maximumCharacters) / 2),
  );
  const cabinBack = dimensions.bayLength / 2;
  const cabinFront = -(bays - 1) * dimensions.bayLength - dimensions.bayLength / 2;
  return {
    bays,
    cabinBack,
    cabinFront,
    minZ: cabinFront - dimensions.bowLength,
    maxZ: cabinBack + dimensions.sternLength,
  };
}
export type HallLayout = ReturnType<typeof createLayout>;

export function exhibitPosition(index: number) {
  const side = index % 2 === 0 ? -1 : 1;
  return { x: side * dimensions.frameX, z: -Math.floor(index / 2) * dimensions.bayLength, side };
}

export function isWalkable(x: number, z: number, hall: HallLayout) {
  const radius = dimensions.playerRadius;
  if (z < hall.minZ + 0.6 || z > hall.maxZ - 0.6) return false;
  let halfWidth = 4.4;
  if (z >= hall.cabinFront && z <= hall.cabinBack) halfWidth = 3.1;
  if (z < hall.cabinFront - 3) halfWidth = 4.4 - (hall.cabinFront - z - 3) * 0.65;
  if (Math.abs(x) > halfWidth - radius) return false;
  // 船首舵台和船尾桅杆使用保守包围圆，墙面展位留在主通道边界外。
  if (Math.hypot(x, z - (hall.cabinFront - 5.8)) < 0.95) return false;
  if ([-4.1, 4.1].some((mastX) => Math.hypot(x - mastX, z - (hall.cabinBack + 4.6)) < 0.55))
    return false;
  return true;
}

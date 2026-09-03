const MAX_IMAGE_EDGE = 2560;
const WEBP_QUALITY = 0.82;

function isGif(file: File): boolean {
  return file.type === "image/gif" || file.name.toLowerCase().endsWith(".gif");
}

function isAnimatedWebp(buffer: ArrayBuffer): boolean {
  const bytes = new Uint8Array(buffer);
  const view = new DataView(buffer);
  const text = (offset: number, length: number) =>
    String.fromCharCode(...bytes.subarray(offset, offset + length));
  if (bytes.length < 16 || text(0, 4) !== "RIFF" || text(8, 4) !== "WEBP") return false;

  let offset = 12;
  while (offset + 8 <= bytes.length) {
    const chunkType = text(offset, 4);
    const chunkSize = view.getUint32(offset + 4, true);
    const chunkData = offset + 8;
    if (chunkData + chunkSize > bytes.length) return false;
    if (chunkType === "ANIM") return true;
    if (chunkType === "VP8X" && chunkSize > 0 && (bytes[chunkData] & 0x02) !== 0) return true;
    offset = chunkData + chunkSize + (chunkSize % 2);
  }
  return false;
}

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    const objectUrl = URL.createObjectURL(file);
    image.onload = () => {
      URL.revokeObjectURL(objectUrl);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("无法读取图片"));
    };
    image.src = objectUrl;
  });
}

function canvasBlob(canvas: HTMLCanvasElement): Promise<Blob | null> {
  return new Promise((resolve) => canvas.toBlob(resolve, "image/webp", WEBP_QUALITY));
}

/** 静态图压缩为 WebP；动图原样返回，避免 Canvas 只保留首帧。 */
export async function compressImage(file: File): Promise<File> {
  if (isGif(file)) return file;

  if (file.type === "image/webp" || file.name.toLowerCase().endsWith(".webp")) {
    if (isAnimatedWebp(await file.arrayBuffer())) return file;
  }

  const image = await loadImage(file);
  const scale = Math.min(1, MAX_IMAGE_EDGE / Math.max(image.naturalWidth, image.naturalHeight));
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(image.naturalWidth * scale));
  canvas.height = Math.max(1, Math.round(image.naturalHeight * scale));
  const context = canvas.getContext("2d");
  if (!context) return file;
  context.drawImage(image, 0, 0, canvas.width, canvas.height);

  const blob = await canvasBlob(canvas);
  if (!blob) return file;
  const filename = `${file.name.replace(/\.[^/.]+$/, "") || "image"}.webp`;
  return new File([blob], filename, {
    type: "image/webp",
    lastModified: file.lastModified,
  });
}

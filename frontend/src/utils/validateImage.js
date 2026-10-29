export const MAX_FILE_SIZE = 10 * 1024 * 1024;
export const MAX_IMAGE_PIXELS = 25_000_000;
export const MIN_DIMENSION = 32;
export const MAX_DIMENSION = 8000;

export async function validateImage(file) {
  if (!file) {
    throw new Error("Please select an image.");
  }

  if (!/\.(jpg|jpeg|png)$/i.test(file.name)) {
    throw new Error("Only JPG, JPEG, and PNG files are supported.");
  }

  if (!["image/jpeg", "image/png"].includes(file.type)) {
    throw new Error("Please upload a valid JPG or PNG image.");
  }

  if (file.size === 0) {
    throw new Error("The selected file is empty.");
  }

  if (file.size > MAX_FILE_SIZE) {
    throw new Error("The maximum image size is 10 MB.");
  }

  const dimensions = await new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(file);
    const image = new Image();

    image.onload = () => {
      const result = {
        width: image.naturalWidth,
        height: image.naturalHeight,
      };

      URL.revokeObjectURL(objectUrl);
      resolve(result);
    };

    image.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("The selected file is not a valid image."));
    };

    image.src = objectUrl;
  });

  const { width, height } = dimensions;

  if (width < MIN_DIMENSION || height < MIN_DIMENSION) {
    throw new Error(
      `Image is too small. Minimum size is ${MIN_DIMENSION} × ${MIN_DIMENSION} px.`,
    );
  }

  if (
    width > MAX_DIMENSION ||
    height > MAX_DIMENSION ||
    width * height > MAX_IMAGE_PIXELS
  ) {
    throw new Error("Image dimensions exceed the supported limits.");
  }

  return {
    name: file.name,
    width,
    height,
    size: file.size,
    format: file.type === "image/png" ? "PNG" : "JPG",
  };
}

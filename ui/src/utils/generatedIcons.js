const generatedIconCache = new Map()

function imageLoaded(src) {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.crossOrigin = 'anonymous'
    image.onload = () => resolve(image)
    image.onerror = reject
    image.src = src
  })
}

function resizedPngDataUrl(image, size) {
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const context = canvas.getContext('2d')
  context.clearRect(0, 0, size, size)
  context.drawImage(image, 0, 0, size, size)
  return canvas.toDataURL('image/png')
}

export async function generateIconsFromImage(src) {
  if (!src || typeof document === 'undefined') {
    return null
  }
  if (!generatedIconCache.has(src)) {
    generatedIconCache.set(
      src,
      imageLoaded(src)
        .then((image) => ({
          appleTouchIcon: resizedPngDataUrl(image, 180),
          favicon: resizedPngDataUrl(image, 32),
          faviconPng: resizedPngDataUrl(image, 32),
          icon192: resizedPngDataUrl(image, 192),
        }))
        .catch(() => null),
    )
  }
  return generatedIconCache.get(src)
}

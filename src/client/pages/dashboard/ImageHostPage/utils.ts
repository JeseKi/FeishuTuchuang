import type { ImageAsset } from '../../../lib/imageHost'

export function formatBytes(value: number): string {
  if (value < 1024) {
    return `${value} B`
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`
  }
  return `${(value / 1024 / 1024).toFixed(2)} MB`
}

export function formatDateTime(value?: string): string {
  if (!value) {
    return '-'
  }
  return new Date(value).toLocaleString()
}

function getClipboardImageExtension(mimeType: string): string {
  const subtype = mimeType.split('/')[1]?.split(';')[0]?.split('+')[0]
  if (!subtype) {
    return 'png'
  }
  return subtype === 'jpeg' ? 'jpg' : subtype
}

export function createClipboardImageFile(blob: Blob, mimeType: string): File {
  const type = mimeType || blob.type || 'image/png'
  return new File([blob], `clipboard-${Date.now()}.${getClipboardImageExtension(type)}`, {
    type,
  })
}

export function ensureNamedClipboardImageFile(file: File): File {
  if (file.name) {
    return file
  }
  const type = file.type || 'image/png'
  return new File([file], `clipboard-${Date.now()}.${getClipboardImageExtension(type)}`, {
    type,
    lastModified: file.lastModified,
  })
}

export function isVideoAsset(target?: ImageAsset | null): boolean {
  return target?.mime_type.startsWith('video/') ?? false
}

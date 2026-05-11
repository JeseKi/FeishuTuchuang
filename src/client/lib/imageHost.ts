import api from './api'

export interface ImageAsset {
  id: string
  filename: string
  url: string
  feishu_image_key: string
  feishu_download_url: string
  original_filename: string
  mime_type: string
  size_bytes: number
  sha256: string
  created_at: string
  last_accessed_at: string
  reused_existing: boolean
}

export interface ImageAssetList {
  items: ImageAsset[]
  limit: number
  offset: number
}

export async function listImageAssets(): Promise<ImageAssetList> {
  const response = await api.get<ImageAssetList>('/images', {
    params: {
      limit: 100,
      offset: 0,
    },
  })
  return response.data
}

export async function uploadImageAsset(file: File): Promise<ImageAsset> {
  const formData = new FormData()
  formData.append('image', file)
  const response = await api.post<ImageAsset>('/images', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

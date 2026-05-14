import api from './api'

export interface ImageAsset {
  id: string
  filename: string
  url: string
  feishu_file_token: string
  feishu_download_url: string
  feishu_folder_id?: number | null
  feishu_folder_name?: string | null
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
  total: number
}

export interface ImageAssetFilters {
  uploaded_from?: string
  uploaded_to?: string
  folder_id?: number
  filename?: string
  feishu_file_token?: string
}

export interface FeishuOAuthAuthorize {
  authorize_url: string
  callback_url: string
  state: string
}

export interface FeishuOAuthStatus {
  connected: boolean
  expires_at?: string | null
  refresh_expires_at?: string | null
  open_id?: string | null
  union_id?: string | null
  user_id?: string | null
  connected_by_user_id?: number | null
}

export interface FeishuFolder {
  id: number
  name: string
  folder_token: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface FeishuFolderPayload {
  name: string
  folder_token: string
  is_active: boolean
}

export async function getFeishuOAuthStatus(): Promise<FeishuOAuthStatus> {
  const response = await api.get<FeishuOAuthStatus>('/images/feishu/oauth/status')
  return response.data
}

export async function createFeishuOAuthAuthorizeUrl(): Promise<FeishuOAuthAuthorize> {
  const response = await api.get<FeishuOAuthAuthorize>('/images/feishu/oauth/authorize')
  return response.data
}

export async function listImageAssets(
  limit = 10,
  offset = 0,
  filters: ImageAssetFilters = {},
): Promise<ImageAssetList> {
  const response = await api.get<ImageAssetList>('/images', {
    params: {
      limit,
      offset,
      ...filters,
    },
  })
  return response.data
}

export async function uploadImageAsset(
  file: File,
  folderId?: number,
): Promise<ImageAsset> {
  const formData = new FormData()
  formData.append('image', file)
  if (folderId !== undefined) {
    formData.append('folder_id', String(folderId))
  }
  const response = await api.post<ImageAsset>('/images', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export async function deleteImageAsset(id: string): Promise<void> {
  await api.delete(`/images/${id}`)
}

export async function listFeishuFolders(): Promise<FeishuFolder[]> {
  const response = await api.get<FeishuFolder[]>('/feishu/folders')
  return response.data
}

export async function createFeishuFolder(payload: FeishuFolderPayload): Promise<FeishuFolder> {
  const response = await api.post<FeishuFolder>('/feishu/folders', payload)
  return response.data
}

export async function updateFeishuFolder(
  id: number,
  payload: FeishuFolderPayload,
): Promise<FeishuFolder> {
  const response = await api.put<FeishuFolder>(`/feishu/folders/${id}`, payload)
  return response.data
}

export async function deleteFeishuFolder(id: number): Promise<void> {
  await api.delete(`/feishu/folders/${id}`)
}

import { Flex, type FormInstance, type UploadProps } from 'antd'
import type { ReactNode } from 'react'
import type {
  FeishuFolder,
  FeishuFolderPayload,
  FeishuOAuthStatus,
  ImageAsset,
  ImageAssetFilters,
} from '../../../lib/imageHost'
import { AssetFilters } from './AssetFilters'
import { AssetDetailsPanel } from './AssetDetailsPanel'
import { AssetHistoryList } from './AssetHistoryList'
import { AssetPreviewPanel } from './AssetPreviewPanel'
import { FolderFormModal } from './FolderFormModal'
import { FolderSection } from './FolderSection'
import { HeaderActions } from './HeaderActions'
import { StatusAlerts } from './StatusAlerts'

interface ImageHostContentProps {
  activeFolder: FeishuFolder | null
  asset: ImageAsset | null
  assets: ImageAsset[]
  connectingFeishu: boolean
  contextHolder: ReactNode
  deletingId: string | null
  editingFolder: FeishuFolder | null
  error: string | null
  folderForm: FormInstance<FeishuFolderPayload>
  folderModalOpen: boolean
  folders: FeishuFolder[]
  filters: ImageAssetFilters
  applyFilters: (filters: ImageAssetFilters) => Promise<void>
  handleClipboardUpload: () => void
  handleDelete: (target: ImageAsset) => Promise<void>
  loadAssets: (targetPage: number) => Promise<void>
  loadFolders: () => Promise<void>
  loadingFolders: boolean
  loadingList: boolean
  oauthStatus: FeishuOAuthStatus | null
  openCreateFolderModal: () => void
  openEditFolderModal: (folder: FeishuFolder) => void
  page: number
  pageSize: number
  previewAssetId: string | null
  removeFolder: (folder: FeishuFolder) => Promise<void>
  savingFolder: boolean
  saveFolder: () => Promise<void>
  setAsset: (asset: ImageAsset) => void
  setError: (error: string | null) => void
  setFolderModalOpen: (open: boolean) => void
  setPage: (page: number) => void
  setPreviewAssetId: (assetId: string) => void
  total: number
  uploadProps: UploadProps
  uploading: boolean
  connectFeishuDrive: () => Promise<void>
  copyText: (text: string, successMessage?: string) => Promise<void>
  copyUrl: (url?: string) => Promise<void>
}

export function ImageHostContent(props: ImageHostContentProps) {
  return (
    <Flex vertical gap={16}>
      {props.contextHolder}
      <HeaderActions {...props} />
      <StatusAlerts {...props} />
      <FolderSection {...props} />

      <Flex gap={16} align="stretch" wrap>
        <AssetDetailsPanel {...props} />
        <AssetPreviewPanel {...props} />
      </Flex>

      <AssetFilters {...props} />
      <AssetHistoryList {...props} />
      <FolderFormModal {...props} />
    </Flex>
  )
}

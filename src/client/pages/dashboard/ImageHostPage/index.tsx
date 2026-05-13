import { useCallback, useEffect, useMemo, useState } from 'react'
import { Form, Upload, message, type UploadProps } from 'antd'
import {
  createFeishuFolder,
  createFeishuOAuthAuthorizeUrl,
  deleteFeishuFolder,
  deleteImageAsset,
  getFeishuOAuthStatus,
  listFeishuFolders,
  listImageAssets,
  updateFeishuFolder,
  uploadImageAsset,
  type FeishuFolder,
  type FeishuFolderPayload,
  type FeishuOAuthStatus,
  type ImageAsset,
  type ImageAssetFilters,
} from '../../../lib/imageHost'
import { resolveApiErrorMessage } from '../../../lib/error'
import { ImageHostContent } from './ImageHostContent'
import { createClipboardImageFile, ensureNamedClipboardImageFile } from './utils'

export default function ImageHostPage() {
  const [asset, setAsset] = useState<ImageAsset | null>(null)
  const [previewAssetId, setPreviewAssetId] = useState<string | null>(null)
  const [assets, setAssets] = useState<ImageAsset[]>([])
  const [uploading, setUploading] = useState(false)
  const [loadingList, setLoadingList] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [oauthStatus, setOauthStatus] = useState<FeishuOAuthStatus | null>(null)
  const [folders, setFolders] = useState<FeishuFolder[]>([])
  const [filters, setFilters] = useState<ImageAssetFilters>({})
  const [loadingFolders, setLoadingFolders] = useState(false)
  const [folderModalOpen, setFolderModalOpen] = useState(false)
  const [editingFolder, setEditingFolder] = useState<FeishuFolder | null>(null)
  const [savingFolder, setSavingFolder] = useState(false)
  const [connectingFeishu, setConnectingFeishu] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [messageApi, contextHolder] = message.useMessage()
  const [folderForm] = Form.useForm<FeishuFolderPayload>()
  const pageSize = 10
  const activeFolder = useMemo(() => folders.find((folder) => folder.is_active) ?? null, [folders])

  const loadAssets = useCallback(async (
    targetPage: number,
    nextFilters: ImageAssetFilters = filters,
  ) => {
    setLoadingList(true)
    setError(null)
    try {
      const result = await listImageAssets(
        pageSize,
        (targetPage - 1) * pageSize,
        nextFilters,
      )
      setAssets(result.items)
      setTotal(result.total)
      setAsset((current) => (
        result.items.some((item) => item.id === current?.id)
          ? current
          : result.items[0] ?? null
      ))
      setPreviewAssetId((current) => (
        result.items.some((item) => item.id === current) ? current : null
      ))
    } catch (err) {
      setError(resolveApiErrorMessage(err))
    } finally {
      setLoadingList(false)
    }
  }, [filters])

  useEffect(() => { void loadAssets(1) }, [loadAssets])

  const loadOAuthStatus = useCallback(async () => {
    try {
      setOauthStatus(await getFeishuOAuthStatus())
    } catch (err) {
      setError(resolveApiErrorMessage(err))
    }
  }, [])

  useEffect(() => { void loadOAuthStatus() }, [loadOAuthStatus])

  const loadFolders = useCallback(async () => {
    setLoadingFolders(true)
    try {
      setFolders(await listFeishuFolders())
    } catch (err) {
      setError(resolveApiErrorMessage(err))
    } finally {
      setLoadingFolders(false)
    }
  }, [])

  useEffect(() => { void loadFolders() }, [loadFolders])

  const handleUpload = useCallback(async (file: File) => {
    setUploading(true)
    setError(null)
    try {
      const result = await uploadImageAsset(file)
      setAsset(result)
      setPage(1)
      await loadAssets(1)
      void messageApi.success(result.reused_existing ? '已复用现有图片' : '上传完成')
    } catch (err) {
      setError(resolveApiErrorMessage(err))
    } finally {
      setUploading(false)
    }
  }, [loadAssets, messageApi])

  const applyFilters = async (nextFilters: ImageAssetFilters) => {
    setFilters(nextFilters)
    setPage(1)
    await loadAssets(1, nextFilters)
  }

  const uploadClipboardImage = useCallback(async (file: File | null) => {
    if (uploading) {
      void messageApi.warning('正在上传，请稍后再试')
      return
    }
    if (!file) {
      void messageApi.warning('剪贴板中没有可上传的图片')
      return
    }
    await handleUpload(ensureNamedClipboardImageFile(file))
  }, [handleUpload, messageApi, uploading])

  const handleClipboardUpload = useCallback(async () => {
    if (!navigator.clipboard?.read) {
      void messageApi.warning('当前浏览器不支持主动读取剪贴板，请直接粘贴图片')
      return
    }

    try {
      const items = await navigator.clipboard.read()
      for (const item of items) {
        const imageType = item.types.find((type) => type.startsWith('image/'))
        if (!imageType) {
          continue
        }
        const blob = await item.getType(imageType)
        await uploadClipboardImage(createClipboardImageFile(blob, imageType))
        return
      }
      void messageApi.warning('剪贴板中没有可上传的图片')
    } catch {
      void messageApi.error('无法读取剪贴板，请允许浏览器访问剪贴板')
    }
  }, [messageApi, uploadClipboardImage])

  useEffect(() => {
    const handlePaste = (event: ClipboardEvent) => {
      const imageFile = Array.from(event.clipboardData?.items ?? [])
        .find((item) => item.kind === 'file' && item.type.startsWith('image/'))
        ?.getAsFile()

      if (!imageFile) {
        return
      }

      event.preventDefault()
      void uploadClipboardImage(imageFile)
    }

    document.addEventListener('paste', handlePaste)
    return () => document.removeEventListener('paste', handlePaste)
  }, [uploadClipboardImage])

  const handleDelete = async (target: ImageAsset) => {
    setDeletingId(target.id)
    setError(null)
    try {
      await deleteImageAsset(target.id)
      void messageApi.success('图片已删除')
      if (asset?.id === target.id) {
        setAsset(null)
      }
      if (previewAssetId === target.id) {
        setPreviewAssetId(null)
      }
      await loadAssets(page)
    } catch (err) {
      setError(resolveApiErrorMessage(err))
    } finally {
      setDeletingId(null)
    }
  }

  const connectFeishuDrive = async () => {
    setConnectingFeishu(true)
    setError(null)
    try {
      const result = await createFeishuOAuthAuthorizeUrl()
      window.open(result.authorize_url, '_blank', 'noopener,noreferrer')
      await navigator.clipboard.writeText(result.callback_url)
      void messageApi.success('已打开飞书授权页，回调地址已复制')
    } catch (err) {
      setError(resolveApiErrorMessage(err))
    } finally {
      setConnectingFeishu(false)
    }
  }

  const openCreateFolderModal = () => {
    setEditingFolder(null)
    folderForm.setFieldsValue({ name: '', folder_token: '', is_active: true })
    setFolderModalOpen(true)
  }

  const openEditFolderModal = (folder: FeishuFolder) => {
    setEditingFolder(folder)
    folderForm.setFieldsValue({
      name: folder.name,
      folder_token: folder.folder_token,
      is_active: folder.is_active,
    })
    setFolderModalOpen(true)
  }

  const saveFolder = async () => {
    setSavingFolder(true)
    setError(null)
    try {
      const values = await folderForm.validateFields()
      if (editingFolder) {
        await updateFeishuFolder(editingFolder.id, values)
      } else {
        await createFeishuFolder(values)
      }
      setFolderModalOpen(false)
      await loadFolders()
      void messageApi.success('文件夹配置已保存')
    } catch (err) {
      if (err && typeof err === 'object' && 'errorFields' in err) {
        return
      }
      setError(resolveApiErrorMessage(err))
    } finally {
      setSavingFolder(false)
    }
  }

  const removeFolder = async (folder: FeishuFolder) => {
    setError(null)
    try {
      await deleteFeishuFolder(folder.id)
      await loadFolders()
      void messageApi.success('文件夹配置已删除')
    } catch (err) {
      setError(resolveApiErrorMessage(err))
    }
  }

  const uploadProps = useMemo<UploadProps>(() => ({
    accept: 'image/*,video/*',
    maxCount: 1,
    showUploadList: false,
    beforeUpload: (file) => {
      void handleUpload(file)
      return Upload.LIST_IGNORE
    },
  }), [handleUpload])

  const copyUrl = async (url?: string) => {
    const targetUrl = url ?? asset?.url
    if (!targetUrl) return
    await navigator.clipboard.writeText(targetUrl)
    void messageApi.success('链接已复制')
  }

  const copyText = async (text: string, successMessage = '内容已复制') => {
    await navigator.clipboard.writeText(text)
    void messageApi.success(successMessage)
  }

  return <ImageHostContent {...{
    activeFolder, asset, assets, connectingFeishu, contextHolder,
    deletingId, editingFolder, error, folderForm, folderModalOpen,
    folders, filters, applyFilters, handleClipboardUpload, handleDelete,
    loadAssets, loadFolders, loadingFolders, loadingList, oauthStatus,
    openCreateFolderModal, openEditFolderModal, page, pageSize, previewAssetId,
    removeFolder, savingFolder, saveFolder, setAsset, setError,
    setFolderModalOpen, setPage, setPreviewAssetId, total, uploadProps,
    uploading, connectFeishuDrive, copyText, copyUrl,
  }} />
}

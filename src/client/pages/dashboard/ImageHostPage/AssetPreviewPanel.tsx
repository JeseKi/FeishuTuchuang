import { Button, Flex, Image, theme } from 'antd'
import { EyeOutlined, FileImageOutlined } from '@ant-design/icons'
import type { ImageAsset } from '../../../lib/imageHost'
import { isVideoAsset } from './utils'

interface AssetPreviewPanelProps {
  asset: ImageAsset | null
  previewAssetId: string | null
  setPreviewAssetId: (assetId: string) => void
}

export function AssetPreviewPanel({
  asset,
  previewAssetId,
  setPreviewAssetId,
}: AssetPreviewPanelProps) {
  const { token } = theme.useToken()

  return (
    <Flex
      align="center"
      justify="center"
      style={{
        flex: '1 1 360px',
        minWidth: 280,
        minHeight: 280,
        padding: 16,
        border: `1px solid ${token.colorBorder}`,
        borderRadius: 8,
        background: token.colorBgContainer,
      }}
    >
      {asset ? (
        isVideoAsset(asset) ? (
          previewAssetId === asset.id ? (
            <video
              src={asset.url}
              controls
              style={{
                width: '100%',
                maxHeight: 420,
                objectFit: 'contain',
              }}
            />
          ) : (
            <Button icon={<EyeOutlined />} onClick={() => setPreviewAssetId(asset.id)}>
              预览
            </Button>
          )
        ) : (
          previewAssetId === asset.id ? (
            <Image
              src={asset.url}
              alt={asset.original_filename}
              style={{
                maxHeight: 420,
                objectFit: 'contain',
              }}
            />
          ) : (
            <Button icon={<EyeOutlined />} onClick={() => setPreviewAssetId(asset.id)}>
              预览
            </Button>
          )
        )
      ) : (
        <FileImageOutlined style={{ fontSize: 64, color: token.colorTextTertiary }} />
      )}
    </Flex>
  )
}

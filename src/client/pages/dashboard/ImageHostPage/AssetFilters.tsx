import { useEffect, useState } from 'react'
import { Button, DatePicker, Flex, Input, Select, Space, Typography } from 'antd'
import { FilterOutlined, ReloadOutlined } from '@ant-design/icons'
import dayjs, { type Dayjs } from 'dayjs'
import type { FeishuFolder, ImageAssetFilters } from '../../../lib/imageHost'

interface AssetFiltersProps {
  filters: ImageAssetFilters
  folders: FeishuFolder[]
  loadingList: boolean
  applyFilters: (filters: ImageAssetFilters) => Promise<void>
}

export function AssetFilters({
  filters,
  folders,
  loadingList,
  applyFilters,
}: AssetFiltersProps) {
  const [filename, setFilename] = useState(filters.filename ?? '')
  const [feishuFileToken, setFeishuFileToken] = useState(filters.feishu_file_token ?? '')
  const dateValue: [Dayjs, Dayjs] | null = filters.uploaded_from && filters.uploaded_to
    ? [dayjs(filters.uploaded_from), dayjs(filters.uploaded_to)]
    : null

  useEffect(() => {
    setFilename(filters.filename ?? '')
    setFeishuFileToken(filters.feishu_file_token ?? '')
  }, [filters.filename, filters.feishu_file_token])

  const applyTextFilters = (nextFilename = filename, nextFeishuFileToken = feishuFileToken) => {
    const normalizedFilename = nextFilename.trim()
    const normalizedFeishuFileToken = nextFeishuFileToken.trim()
    void applyFilters({
      ...filters,
      filename: normalizedFilename || undefined,
      feishu_file_token: normalizedFeishuFileToken || undefined,
    })
  }

  const updateDateRange = (value: [Dayjs | null, Dayjs | null] | null) => {
    void applyFilters({
      ...filters,
      uploaded_from: value?.[0]?.format('YYYY-MM-DD'),
      uploaded_to: value?.[1]?.format('YYYY-MM-DD'),
    })
  }

  const updateFolder = (folderId?: number) => {
    void applyFilters({
      ...filters,
      folder_id: folderId,
    })
  }

  const resetFilters = () => {
    setFilename('')
    setFeishuFileToken('')
    void applyFilters({})
  }

  return (
    <Flex align="center" justify="space-between" wrap gap={12}>
      <Space size={10}>
        <FilterOutlined />
        <Typography.Title level={4} style={{ margin: 0 }}>
          历史图片/视频
        </Typography.Title>
      </Space>
      <Space wrap>
        <Input.Search
          allowClear
          placeholder="搜索文件名"
          value={filename}
          onChange={(event) => {
            const value = event.target.value
            setFilename(value)
            if (!value && filters.filename) {
              applyTextFilters('', feishuFileToken)
            }
          }}
          onSearch={(value) => applyTextFilters(value, feishuFileToken)}
          style={{ width: 200 }}
        />
        <Input.Search
          allowClear
          placeholder="飞书文件 Token"
          value={feishuFileToken}
          onChange={(event) => {
            const value = event.target.value
            setFeishuFileToken(value)
            if (!value && filters.feishu_file_token) {
              applyTextFilters(filename, '')
            }
          }}
          onSearch={(value) => applyTextFilters(filename, value)}
          style={{ width: 220 }}
        />
        <DatePicker.RangePicker
          allowClear
          value={dateValue}
          onChange={updateDateRange}
        />
        <Select
          allowClear
          placeholder="全部文件夹"
          value={filters.folder_id}
          onChange={updateFolder}
          style={{ minWidth: 180 }}
          options={folders.map((folder) => ({
            label: folder.name,
            value: folder.id,
          }))}
        />
        <Button icon={<ReloadOutlined />} loading={loadingList} onClick={resetFilters}>
          重置
        </Button>
      </Space>
    </Flex>
  )
}

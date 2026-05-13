import { Button, DatePicker, Flex, Select, Space, Typography } from 'antd'
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
  const dateValue: [Dayjs, Dayjs] | null = filters.uploaded_from && filters.uploaded_to
    ? [dayjs(filters.uploaded_from), dayjs(filters.uploaded_to)]
    : null

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

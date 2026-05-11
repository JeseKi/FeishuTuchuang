import { Alert, Button, Card, Descriptions, Form, InputNumber, Typography } from 'antd'
import type { FormInstance } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import type { Item } from '../../../lib/types'

interface FetchItemCardProps {
  fetchLoading: boolean
  fetchError: string | null
  fetchedItem: Item | null
  form: FormInstance
  onSubmit: (values: { id: number }) => void
}

export default function FetchItemCard({
  fetchLoading,
  fetchError,
  fetchedItem,
  form,
  onSubmit,
}: FetchItemCardProps) {
  return (
    <Card title="查询示例条目">
      <Typography.Paragraph type="secondary">
        输入条目 ID 并提交，将带回后端的查询结果，便于快速验证数据。
      </Typography.Paragraph>
      <Form
        form={form}
        layout="vertical"
        onFinish={onSubmit}
        requiredMark={false}
        className="mt-6"
      >
        <Form.Item
          label="条目 ID"
          name="id"
          rules={[
            { required: true, message: '请输入条目 ID' },
            {
              type: 'number',
              min: 1,
              transform: (value) => (value ?? undefined),
              message: '请输入大于 0 的整数',
            },
          ]}
        >
          <InputNumber
            min={1}
            size="large"
            style={{ width: '100%' }}
            placeholder="请输入条目 ID"
          />
        </Form.Item>
        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={fetchLoading}
            icon={<SearchOutlined />}
          >
            查询条目
          </Button>
        </Form.Item>
      </Form>
      {fetchError && <Alert type="error" showIcon message={fetchError} className="mt-4" />}
      {fetchedItem && (
        <Card type="inner" title="查询结果" className="mt-4">
          <Descriptions column={1} size="small" labelStyle={{ width: 96 }}>
            <Descriptions.Item label="条目 ID">{fetchedItem.id}</Descriptions.Item>
            <Descriptions.Item label="条目名称">{fetchedItem.name}</Descriptions.Item>
          </Descriptions>
        </Card>
      )}
    </Card>
  )
}

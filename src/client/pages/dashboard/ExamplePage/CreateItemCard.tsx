import { Alert, Button, Card, Descriptions, Form, Input, Result, Typography } from 'antd'
import type { FormInstance } from 'antd'
import { PlusCircleOutlined } from '@ant-design/icons'
import type { Item } from '../../../lib/types'

interface CreateItemCardProps {
  createLoading: boolean
  createError: string | null
  createdItem: Item | null
  form: FormInstance
  onSubmit: (values: { name: string }) => void
}

export default function CreateItemCard({
  createLoading,
  createError,
  createdItem,
  form,
  onSubmit,
}: CreateItemCardProps) {
  return (
    <Card title="创建示例条目">
      <Typography.Paragraph type="secondary">
        填写名称后提交，将调用后端创建接口并返回新条目的详细信息。
      </Typography.Paragraph>
      <Form
        form={form}
        layout="vertical"
        onFinish={onSubmit}
        requiredMark={false}
        className="mt-6"
      >
        <Form.Item
          label="条目名称"
          name="name"
          rules={[
            { required: true, message: '请输入条目名称' },
            { min: 2, message: '名称至少需要 2 个字符' },
          ]}
        >
          <Input size="large" placeholder="例如：现代化前端" allowClear />
        </Form.Item>
        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={createLoading}
            icon={<PlusCircleOutlined />}
          >
            创建条目
          </Button>
        </Form.Item>
      </Form>
      {createError && <Alert type="error" showIcon message={createError} className="mt-4" />}
      {createdItem && (
        <Result
          status="success"
          title="创建成功"
          extra={
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="条目 ID">{createdItem.id}</Descriptions.Item>
              <Descriptions.Item label="条目名称">{createdItem.name}</Descriptions.Item>
            </Descriptions>
          }
        />
      )}
    </Card>
  )
}

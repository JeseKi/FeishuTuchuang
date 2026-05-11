import { Flex, Typography } from 'antd'
import { DashboardOutlined } from '@ant-design/icons'

export default function DashboardPage() {
  return (
    <Flex vertical gap={16}>
      <Typography.Title level={2} style={{ margin: 0 }}>
        <DashboardOutlined /> 欢迎使用 Fullstack Template
      </Typography.Title>
      <Typography.Paragraph type="secondary">
        这是一个全栈模板项目，前端使用 React + Ant Design，后端使用 FastAPI。
        请从左侧菜单选择功能模块。
      </Typography.Paragraph>
    </Flex>
  )
}
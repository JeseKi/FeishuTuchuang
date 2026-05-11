import { Alert, Button, Card, Descriptions, Flex, Form, Input, InputNumber, List, Progress, Space, Statistic, Tag, Typography } from 'antd'
import type { FormInstance, GlobalToken } from 'antd'
import { ClockCircleOutlined, DatabaseOutlined, SyncOutlined } from '@ant-design/icons'
import type { AsyncTaskDetail } from '../../../lib/types'
import type { TaskStatusMeta } from './utils'
import { resolveLogColor, formatDateTime } from './utils'

interface AsyncTaskCardProps {
  taskCreating: boolean
  taskRefreshing: boolean
  taskError: string | null
  activeTask: AsyncTaskDetail | null
  taskStatusMeta: TaskStatusMeta
  token: GlobalToken
  form: FormInstance
  onCreateTask: (values: { name: string; total_count: number; fail_every: number; delay_ms: number }) => void
  onRefreshTask: () => void
}

export default function AsyncTaskCard({
  taskCreating,
  taskRefreshing,
  taskError,
  activeTask,
  taskStatusMeta,
  token,
  form,
  onCreateTask,
  onRefreshTask,
}: AsyncTaskCardProps) {
  return (
    <Card
      title="长时异步任务"
      extra={
        <Button
          icon={<SyncOutlined />}
          onClick={onRefreshTask}
          disabled={!activeTask}
          loading={taskRefreshing}
        >
          刷新任务
        </Button>
      }
    >
      <Space direction="vertical" size={20} style={{ width: '100%' }}>
        <Typography.Paragraph type="secondary">
          这个示例会创建后台任务，逐项写入数据库日志，并持续更新执行进度、成功数和失败数。
        </Typography.Paragraph>
        <Form
          form={form}
          layout="vertical"
          requiredMark={false}
          onFinish={onCreateTask}
          initialValues={{
            name: '样本批处理任务',
            total_count: 12,
            fail_every: 4,
            delay_ms: 250,
          }}
        >
          <Flex gap={16} wrap="wrap">
            <Form.Item
              label="任务名称"
              name="name"
              rules={[
                { required: true, message: '请输入任务名称' },
                { min: 2, message: '名称至少需要 2 个字符' },
              ]}
              style={{ flex: '1 1 260px', marginBottom: 0 }}
            >
              <Input size="large" placeholder="例如：夜间数据对账" allowClear />
            </Form.Item>
            <Form.Item
              label="总处理数"
              name="total_count"
              rules={[{ required: true, message: '请输入总处理数' }]}
              style={{ flex: '1 1 180px', marginBottom: 0 }}
            >
              <InputNumber min={1} max={200} size="large" style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              label="每隔多少项失败一次"
              name="fail_every"
              rules={[{ required: true, message: '请输入失败频率' }]}
              style={{ flex: '1 1 220px', marginBottom: 0 }}
            >
              <InputNumber min={0} max={50} size="large" style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              label="单项延迟(ms)"
              name="delay_ms"
              rules={[{ required: true, message: '请输入延迟时间' }]}
              style={{ flex: '1 1 180px', marginBottom: 0 }}
            >
              <InputNumber min={0} max={5000} size="large" style={{ width: '100%' }} />
            </Form.Item>
          </Flex>
          <Form.Item className="mt-6">
            <Button
              type="primary"
              htmlType="submit"
              loading={taskCreating}
              icon={<ClockCircleOutlined />}
            >
              创建并启动任务
            </Button>
          </Form.Item>
        </Form>
        {taskError && <Alert type="error" showIcon message={taskError} />}
        {!activeTask && !taskError && (
          <Alert
            type="info"
            showIcon
            message="尚未创建任务。提交上方表单后，这里会持续展示进度、日志和执行统计。"
          />
        )}
        {activeTask && (
          <TaskDetail task={activeTask} taskStatusMeta={taskStatusMeta} token={token} />
        )}
      </Space>
    </Card>
  )
}

interface TaskDetailProps {
  task: AsyncTaskDetail
  taskStatusMeta: TaskStatusMeta
  token: GlobalToken
}

function TaskDetail({ task, taskStatusMeta, token }: TaskDetailProps) {
  return (
    <Flex vertical gap={16}>
      <Card type="inner" title="任务状态总览">
        <Space direction="vertical" size={20} style={{ width: '100%' }}>
          <Flex gap={16} wrap="wrap">
            <Statistic
              title="当前状态"
              value={taskStatusMeta.label}
              valueStyle={{ color: taskStatusMeta.color }}
            />
            <Statistic title="已处理" value={task.processed_count} suffix={`/ ${task.total_count}`} />
            <Statistic title="成功数" value={task.success_count} valueStyle={{ color: token?.colorSuccess }} />
            <Statistic title="失败数" value={task.failure_count} valueStyle={{ color: token?.colorError }} />
          </Flex>
          <Progress
            percent={task.progress_percent}
            status={taskStatusMeta.progressStatus}
            strokeColor={taskStatusMeta.color}
          />
          <Descriptions column={1} size="small" labelStyle={{ width: 140 }}>
            <Descriptions.Item label="最新反馈">
              {task.last_message ?? '暂无'}
            </Descriptions.Item>
            <Descriptions.Item label="任务 ID">{task.id}</Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {formatDateTime(task.created_at)}
            </Descriptions.Item>
            <Descriptions.Item label="开始时间">
              {formatDateTime(task.started_at)}
            </Descriptions.Item>
            <Descriptions.Item label="结束时间">
              {formatDateTime(task.finished_at)}
            </Descriptions.Item>
          </Descriptions>
        </Space>
      </Card>

      <Card
        type="inner"
        title="数据库执行日志"
        extra={
          <Tag color="blue" icon={<DatabaseOutlined />}>
            {task.logs.length} 条
          </Tag>
        }
      >
        <List
          dataSource={task.logs}
          locale={{ emptyText: '暂无日志' }}
          style={{ maxHeight: 320, overflow: 'auto' }}
          renderItem={(log) => (
            <List.Item key={log.id}>
              <Space direction="vertical" size={4} style={{ width: '100%' }}>
                <Flex justify="space-between" align="center" gap={12}>
                  <Space size={8}>
                    <Tag color={resolveLogColor(log.level)}>{log.level.toUpperCase()}</Tag>
                    <Typography.Text strong>#{log.sequence}</Typography.Text>
                  </Space>
                  <Typography.Text type="secondary">
                    {formatDateTime(log.created_at)}
                  </Typography.Text>
                </Flex>
                <Typography.Text>{log.message}</Typography.Text>
              </Space>
            </List.Item>
          )}
        />
      </Card>
    </Flex>
  )
}

import { useEffect, useMemo, useState } from 'react'
import { App, Flex, Form, theme } from 'antd'
import * as exampleApi from '../../../lib/example'
import type { AsyncTaskDetail, Item } from '../../../lib/types'
import { resolveErrorMessage, isTaskActive, resolveTaskStatusMeta } from './utils'
import HealthCheckCard from './HealthCheckCard'
import CreateItemCard from './CreateItemCard'
import FetchItemCard from './FetchItemCard'
import AsyncTaskCard from './AsyncTaskCard'

export default function ExamplePage() {
  const { message } = App.useApp()
  const { token } = theme.useToken()

  const [pingLoading, setPingLoading] = useState(false)
  const [pingError, setPingError] = useState<string | null>(null)
  const [pingResult, setPingResult] = useState<string | null>(null)

  const [createForm] = Form.useForm<{ name: string }>()
  const [createLoading, setCreateLoading] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [createdItem, setCreatedItem] = useState<Item | null>(null)

  const [fetchForm] = Form.useForm<{ id: number }>()
  const [fetchLoading, setFetchLoading] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [fetchedItem, setFetchedItem] = useState<Item | null>(null)

  const [taskForm] = Form.useForm()
  const [taskCreating, setTaskCreating] = useState(false)
  const [taskRefreshing, setTaskRefreshing] = useState(false)
  const [taskError, setTaskError] = useState<string | null>(null)
  const [activeTask, setActiveTask] = useState<AsyncTaskDetail | null>(null)

  const handlePing = async () => {
    setPingLoading(true)
    setPingError(null)
    try {
      const result = await exampleApi.ping()
      setPingResult(result)
      message.success('服务正常响应')
    } catch (error) {
      const text = resolveErrorMessage(error)
      setPingError(text)
      setPingResult(null)
      message.error(text)
    } finally {
      setPingLoading(false)
    }
  }

  const handleCreateItem = async ({ name }: { name: string }) => {
    const trimmed = name.trim()
    if (!trimmed) {
      setCreateError('名称不能为空')
      return
    }
    setCreateLoading(true)
    setCreateError(null)
    try {
      const item = await exampleApi.createItem({ name: trimmed })
      setCreatedItem(item)
      message.success('示例条目创建成功')
      createForm.resetFields()
    } catch (error) {
      const text = resolveErrorMessage(error)
      setCreateError(text)
      setCreatedItem(null)
      message.error(text)
    } finally {
      setCreateLoading(false)
    }
  }

  const handleFetchItem = async ({ id }: { id: number }) => {
    setFetchLoading(true)
    setFetchError(null)
    try {
      const item = await exampleApi.getItem(id)
      setFetchedItem(item)
      message.success('查询成功')
    } catch (error) {
      const text = resolveErrorMessage(error)
      setFetchError(text)
      setFetchedItem(null)
      message.error(text)
    } finally {
      setFetchLoading(false)
    }
  }

  const statisticValue = useMemo(() => {
    if (pingResult) return '可用'
    if (pingError) return '异常'
    return '待检测'
  }, [pingError, pingResult])

  const taskStatusMeta = useMemo(() => {
    return resolveTaskStatusMeta(activeTask?.status)
  }, [activeTask?.status])

  useEffect(() => {
    if (!activeTask?.id || !activeTask?.status || !isTaskActive(activeTask.status)) {
      return
    }

    const pollTask = async () => {
      try {
        const detail = await exampleApi.getAsyncTask(activeTask.id)
        setActiveTask(detail)
        setTaskError(null)
      } catch (error) {
        setTaskError(resolveErrorMessage(error))
      }
    }

    const timer = window.setInterval(() => {
      void pollTask()
    }, 1000)

    return () => {
      window.clearInterval(timer)
    }
  }, [activeTask?.id, activeTask?.status])

  const refreshTask = async (taskId: number, silent = false) => {
    if (!silent) setTaskRefreshing(true)
    try {
      const detail = await exampleApi.getAsyncTask(taskId)
      setActiveTask(detail)
      setTaskError(null)
    } catch (error) {
      const text = resolveErrorMessage(error)
      setTaskError(text)
      if (!silent) message.error(text)
    } finally {
      if (!silent) setTaskRefreshing(false)
    }
  }

  const handleCreateTask = async (values: { name: string; total_count: number; fail_every: number; delay_ms: number }) => {
    const trimmed = values.name.trim()
    if (!trimmed) {
      setTaskError('任务名称不能为空')
      return
    }

    setTaskCreating(true)
    setTaskError(null)
    try {
      const task = await exampleApi.createAsyncTask({
        name: trimmed,
        total_count: values.total_count,
        fail_every: values.fail_every,
        delay_ms: values.delay_ms,
      })
      setActiveTask({ ...task, logs: [] })
      taskForm.resetFields()
      message.success('异步任务已创建')
      await refreshTask(task.id, true)
    } catch (error) {
      const text = resolveErrorMessage(error)
      setTaskError(text)
      setActiveTask(null)
      message.error(text)
    } finally {
      setTaskCreating(false)
    }
  }

  return (
    <Flex vertical gap={24}>
      <HealthCheckCard
        pingLoading={pingLoading}
        pingError={pingError}
        pingResult={pingResult}
        statisticValue={statisticValue}
        token={token}
        onPing={handlePing}
      />

      <CreateItemCard
        createLoading={createLoading}
        createError={createError}
        createdItem={createdItem}
        form={createForm}
        onSubmit={handleCreateItem}
      />

      <FetchItemCard
        fetchLoading={fetchLoading}
        fetchError={fetchError}
        fetchedItem={fetchedItem}
        form={fetchForm}
        onSubmit={handleFetchItem}
      />

      <AsyncTaskCard
        taskCreating={taskCreating}
        taskRefreshing={taskRefreshing}
        taskError={taskError}
        activeTask={activeTask}
        taskStatusMeta={taskStatusMeta}
        token={token}
        form={taskForm}
        onCreateTask={handleCreateTask}
        onRefreshTask={() => activeTask && void refreshTask(activeTask.id)}
      />
    </Flex>
  )
}

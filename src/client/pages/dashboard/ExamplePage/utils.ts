import type { AsyncTaskStatus, AsyncTaskLog } from '../../../lib/types'
import { resolveApiErrorMessage } from '../../../lib/error'

export function resolveErrorMessage(error: unknown): string {
  return resolveApiErrorMessage(error, '请求失败，请稍后再试。')
}

export function isTaskActive(status: AsyncTaskStatus): boolean {
  return status === 'pending' || status === 'running'
}

export interface TaskStatusMeta {
  label: string
  color: string
  progressStatus: 'normal' | 'active' | 'success' | 'exception'
}

export function resolveTaskStatusMeta(status: AsyncTaskStatus | undefined): TaskStatusMeta {
  switch (status) {
    case 'running':
      return { label: '执行中', color: '#1677ff', progressStatus: 'active' }
    case 'completed':
      return { label: '已完成', color: '#52c41a', progressStatus: 'success' }
    case 'failed':
      return { label: '执行失败', color: '#ff4d4f', progressStatus: 'exception' }
    default:
      return { label: '待启动', color: '#faad14', progressStatus: 'normal' }
  }
}

export function resolveLogColor(level: AsyncTaskLog['level']): string {
  switch (level) {
    case 'warning':
      return 'orange'
    case 'error':
      return 'red'
    default:
      return 'blue'
  }
}

export function formatDateTime(value: string | null): string {
  if (!value) {
    return '暂无'
  }
  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'medium',
  }).format(new Date(value))
}

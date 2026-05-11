import api from './api'
import type { AsyncTask, AsyncTaskDetail, AsyncTaskPayload, Item, ItemPayload } from './types'

export async function ping(): Promise<string> {
  const { data } = await api.get<{ message: string }>('/example/ping')
  return data.message
}

export async function createItem(payload: ItemPayload): Promise<Item> {
  const { data } = await api.post<Item>('/example/items', payload)
  return data
}

export async function getItem(itemId: number): Promise<Item> {
  const { data } = await api.get<Item>(`/example/items/${itemId}`)
  return data
}

export async function createAsyncTask(payload: AsyncTaskPayload): Promise<AsyncTask> {
  const { data } = await api.post<AsyncTask>('/example/tasks', payload)
  return data
}

export async function getAsyncTask(taskId: number): Promise<AsyncTaskDetail> {
  const { data } = await api.get<AsyncTaskDetail>(`/example/tasks/${taskId}`)
  return data
}

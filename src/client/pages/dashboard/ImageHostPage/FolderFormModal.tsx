import { Form, Input, Modal, Switch, type FormInstance } from 'antd'
import { FolderOutlined, SettingOutlined } from '@ant-design/icons'
import type { FeishuFolder, FeishuFolderPayload } from '../../../lib/imageHost'

interface FolderFormModalProps {
  editingFolder: FeishuFolder | null
  folderForm: FormInstance<FeishuFolderPayload>
  folderModalOpen: boolean
  savingFolder: boolean
  saveFolder: () => Promise<void>
  setFolderModalOpen: (open: boolean) => void
}

export function FolderFormModal({
  editingFolder,
  folderForm,
  folderModalOpen,
  savingFolder,
  saveFolder,
  setFolderModalOpen,
}: FolderFormModalProps) {
  return (
    <Modal
      title={editingFolder ? '编辑飞书文件夹' : '新增飞书文件夹'}
      open={folderModalOpen}
      okText="保存"
      cancelText="取消"
      confirmLoading={savingFolder}
      onOk={() => void saveFolder()}
      onCancel={() => setFolderModalOpen(false)}
    >
      <Form form={folderForm} layout="vertical" requiredMark={false}>
        <Form.Item
          name="name"
          label="文件夹名称"
          rules={[{ required: true, message: '请输入文件夹名称' }]}
        >
          <Input prefix={<FolderOutlined />} placeholder="图床" />
        </Form.Item>
        <Form.Item
          name="folder_token"
          label="Folder Token"
          rules={[{ required: true, message: '请输入 folder token' }]}
        >
          <Input prefix={<SettingOutlined />} placeholder="飞书文件夹 token" />
        </Form.Item>
        <Form.Item name="is_active" label="设为上传文件夹" valuePropName="checked">
          <Switch />
        </Form.Item>
      </Form>
    </Modal>
  )
}

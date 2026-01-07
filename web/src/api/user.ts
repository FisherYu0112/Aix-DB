import { useUserStore } from '@/store/business/userStore'

const BASE_URL = `${location.origin}/sanic/user`

const getHeaders = () => {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  }
}

/**
 * 查询用户列表
 * @param page
 * @param size
 * @param name
 */
export async function queryUserList(page: number, size: number, name?: string) {
  const url = new URL(`${BASE_URL}/list`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: getHeaders(),
    body: JSON.stringify({ page, size, name }),
  })
  return fetch(req)
}

/**
 * 添加用户
 * @param data
 */
export async function addUser(data: any) {
  const url = new URL(`${BASE_URL}/add`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: getHeaders(),
    body: JSON.stringify(data),
  })
  return fetch(req)
}

/**
 * 更新用户
 * @param data
 */
export async function updateUser(data: any) {
  const url = new URL(`${BASE_URL}/update`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: getHeaders(),
    body: JSON.stringify(data),
  })
  return fetch(req)
}

/**
 * 删除用户
 * @param id
 */
export async function deleteUser(id: number) {
  const url = new URL(`${BASE_URL}/delete`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: getHeaders(),
    body: JSON.stringify({ id }),
  })
  return fetch(req)
}

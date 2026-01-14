/**
 * 数据源相关 API 封装
 */
import { useUserStore } from '@/store/business/userStore'

/**
 * 获取数据源列表
 */
export async function fetch_datasource_list() {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/sanic/datasource/list`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'get',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  return fetch(req)
}

/**
 * 获取数据源表列表
 */
export async function fetch_datasource_table_list(dsId: number | string) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/sanic/datasource/tableList/${dsId}`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  return fetch(req)
}

/**
 * 获取表字段列表
 */
export async function fetch_datasource_field_list(tableId: number | string) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/sanic/datasource/fieldList/${tableId}`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  return fetch(req)
}

/**
 * 获取表预览数据
 */
export async function fetch_datasource_preview_data(dsId: number | string, buildData: any) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/sanic/datasource/previewData`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      ...buildData,
      ds_id: dsId,
    }),
  })
  return fetch(req)
}

/**
 * 保存表信息（含自定义注释）
 */
export async function save_datasource_table(tableData: any) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/sanic/datasource/saveTable`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(tableData),
  })
  return fetch(req)
}

/**
 * 保存字段信息（含自定义注释 / 状态）
 */
export async function save_datasource_field(fieldData: any) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/sanic/datasource/saveField`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(fieldData),
  })
  return fetch(req)
}

/**
 * 获取单个数据源详情
 */
export async function fetch_datasource_detail(id: number | string) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/sanic/datasource/get/${id}`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  return fetch(req)
}

/**
 * 删除数据源
 */
export async function delete_datasource(id: number | string) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/sanic/datasource/delete/${id}`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  return fetch(req)
}

/**
 * 获取 Neo4j 图数据库关系
 */
export async function fetch_neo4j_relation(dsId: number | string) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/sanic/datasource/getNeo4jRelation/${dsId}`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  return fetch(req)
}

/**
 * 检查数据源连接
 */
export async function check_datasource_connection(data: any) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/sanic/datasource/check`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })
  return fetch(req)
}

/**
 * 根据配置获取表列表
 */
export async function fetch_tables_by_conf(data: any) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/sanic/datasource/getTablesByConf`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })
  return fetch(req)
}

/**
 * 新增数据源
 */
export async function add_datasource(data: any) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/sanic/datasource/add`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })
  return fetch(req)
}

/**
 * 更新数据源
 */
export async function update_datasource(data: any) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/sanic/datasource/update`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })
  return fetch(req)
}

/**
 * 同步数据源表
 */
export async function sync_datasource_tables(dsId: number | string, tables: any[]) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/sanic/datasource/syncTables/${dsId}`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(tables),
  })
  return fetch(req)
}

/**
 * 获取已授权用户
 */
export async function get_authorized_users(datasourceId: number) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/sanic/datasource/getAuthorizedUsers/${datasourceId}`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })
  return fetch(req)
}

/**
 * 数据源授权
 */
export async function authorize_datasource(datasourceId: number, userIds: number[]) {
  const userStore = useUserStore()
  const token = userStore.getUserToken()
  const url = new URL(`${location.origin}/sanic/datasource/authorize`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      datasource_id: datasourceId,
      user_ids: userIds,
    }),
  })
  return fetch(req)
}

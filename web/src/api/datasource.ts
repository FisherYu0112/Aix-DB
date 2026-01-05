/**
 * 数据源相关 API 封装
 */

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
      'Authorization': `Bearer ${token}`,
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
      'Authorization': `Bearer ${token}`,
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
      'Authorization': `Bearer ${token}`,
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
  const url = new URL(`${location.origin}/sanic/datasource/previewData/${dsId}`)
  const req = new Request(url, {
    mode: 'cors',
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(buildData),
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
      'Authorization': `Bearer ${token}`,
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
      'Authorization': `Bearer ${token}`,
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
      'Authorization': `Bearer ${token}`,
    },
  })
  return fetch(req)
}



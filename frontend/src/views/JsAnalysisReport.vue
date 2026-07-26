<template>
  <div style="padding: 24px; background-color: var(--arl-bg-layout); min-height: calc(100vh - 64px);">
    <a-card title="JS 深度分析报告" :loading="loading">
      <a-form layout="inline" style="margin-bottom: 16px;">
        <a-form-item label="任务 ID">
          <a-input v-model:value="searchForm.task_id" placeholder="输入任务ID" allowClear style="width: 280px;" @pressEnter="fetchReport" />
        </a-form-item>
        <a-form-item label="站点">
          <a-input v-model:value="searchForm.site" placeholder="输入站点URL" allowClear style="width: 280px;" @pressEnter="fetchReport" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="fetchReport">查询</a-button>
        </a-form-item>
      </a-form>
      <a-table :dataSource="reports" :columns="columns" :pagination="pagination" :loading="loading" rowKey="_id" @change="onTableChange">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'sourcemap'">
            <a-tag :color="record.sourcemap_found ? 'red' : 'default'">{{ record.sourcemap_found ? '是' : '否' }}</a-tag>
          </template>
          <template v-if="column.key === 'assessment'">
            <a-tooltip :title="record.assessment"><span>{{ record.assessment?.substring(0, 60) }}...</span></a-tooltip>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { message } from 'ant-design-vue';
import request from '../utils/request';

const searchForm = reactive({ task_id: '', site: '' });
const reports = ref([]);
const loading = ref(false);
const pagination = reactive({ current: 1, pageSize: 10, total: 0 });

const columns = [
  { title: '站点', dataIndex: 'site', key: 'site', width: 250, ellipsis: true },
  { title: 'JS文件', dataIndex: 'js_files_found', key: 'js_files_found', width: 70 },
  { title: '已分析', dataIndex: 'js_files_analyzed', key: 'js_files_analyzed', width: 70 },
  { title: 'API端点', dataIndex: 'api_endpoints', key: 'api_endpoints', width: 70 },
  { title: '路由数', dataIndex: 'routes_found', key: 'routes_found', width: 70 },
  { title: '配置项', dataIndex: 'config_items', key: 'config_items', width: 70 },
  { title: 'Source Map', key: 'sourcemap', width: 90 },
  { title: '框架', dataIndex: 'framework', key: 'framework', width: 120 },
  { title: '评估', key: 'assessment', width: 300, ellipsis: true },
];

async function fetchReport() {
  loading.value = true;
  try {
    const params = { page: pagination.current, size: pagination.pageSize };
    if (searchForm.task_id) params.task_id = searchForm.task_id;
    if (searchForm.site) params.site = searchForm.site;
    const res = await request.get('/api/js_analysis/js_report/', { params });
    if (res.code === 200) {
      reports.value = res.items || [];
      pagination.total = res.total || 0;
    }
  } catch (e) {
    message.error('加载失败');
  }
  loading.value = false;
}

function onTableChange(pg) {
  pagination.current = pg.current;
  pagination.pageSize = pg.pageSize;
  fetchReport();
}
</script>

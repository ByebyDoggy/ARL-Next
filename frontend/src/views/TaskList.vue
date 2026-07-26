<template>
  <div style="background-color: var(--arl-bg-layout); padding: 24px; min-height: calc(100vh - 64px);">

    <div style="margin-bottom: 24px;">
      <a-button type="primary" style="margin-right: 12px;" @click="showModal">娣诲姞浠诲姟</a-button>
      <a-button type="primary" style="margin-right: 12px;" @click="openFofaModal">FOFA 浠诲姟涓嬪彂</a-button>
      <a-button type="primary" @click="goToGlobalView">鍏ㄥ眬鏌ョ湅</a-button>
    </div>

    <div style="margin-bottom: 16px;">
      <a-form :model="searchForm" layout="inline" style="row-gap: 16px;">

        <a-form-item label="浠诲姟鍚?">
          <a-input v-model:value="searchForm.name" placeholder="璇疯緭鍏ヤ换鍔″悕杩涜鎼滅储" style="width: 230px;" allowClear @pressEnter="onSearch">
            <template #suffix><search-outlined @click="onSearch" style="color: var(--arl-text-color); opacity: 0.25; cursor: pointer;"/></template>
          </a-input>
        </a-form-item>

        <a-form-item label="鐩爣:">
          <a-input v-model:value="searchForm.target" placeholder="璇疯緭鍏ョ洰鏍囪繘琛屾悳绱? style="width: 230px;" allowClear @pressEnter="onSearch">
            <template #suffix><search-outlined @click="onSearch" style="color: var(--arl-text-color); opacity: 0.25; cursor: pointer;"/></template>
          </a-input>
        </a-form-item>

        <a-form-item label="Task_Id:">
          <a-input v-model:value="searchForm.task_id" placeholder="璇疯緭鍏ask_Id杩涜鎼滅储" style="width: 230px;" allowClear @pressEnter="onSearch">
            <template #suffix><search-outlined @click="onSearch" style="color: var(--arl-text-color); opacity: 0.25; cursor: pointer;"/></template>
          </a-input>
        </a-form-item>

        <a-form-item label="浠诲姟绫诲瀷:">
          <a-select v-model:value="searchForm.type" placeholder="璇烽€夋嫨浠诲姟绫诲瀷杩涜鎼滅储" style="width: 230px;" allowClear>
            <a-select-option value="task">璧勪骇渚︽煡浠诲姟</a-select-option>
            <a-select-option value="monitor">璧勪骇鐩戞帶浠诲姟</a-select-option>
            <a-select-option value="risk_cruising">椋庨櫓宸¤埅浠诲姟</a-select-option>
            <a-select-option value="site_update">璧勪骇绔欑偣鏇存柊</a-select-option>
            <a-select-option value="wih">WIH 鐩戞帶浠诲姟</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="鐘舵€?">
          <a-input v-model:value="searchForm.status" placeholder="璇疯緭鍏ョ姸鎬佽繘琛屾悳绱? style="width: 230px;" allowClear @pressEnter="onSearch">
            <template #suffix><search-outlined @click="onSearch" style="color: var(--arl-text-color); opacity: 0.25; cursor: pointer;"/></template>
          </a-input>
        </a-form-item>

        <a-form-item label="绔欑偣鏁伴噺:">
          <a-input-group compact style="display: flex; width: 230px;">
            <a-input v-model:value="searchForm.site_count" placeholder="璇疯緭鍏ユ暟閲? style="flex: 1;" @pressEnter="onSearch">
              <template #suffix><search-outlined @click="onSearch" style="color: var(--arl-text-color); opacity: 0.25; cursor: pointer;"/></template>
            </a-input>
            <a-select v-model:value="searchForm.site_operator" style="width: 75px;">
              <a-select-option value="=">绛変簬</a-select-option>
              <a-select-option value=">">澶т簬</a-select-option>
              <a-select-option value="<">灏忎簬</a-select-option>
            </a-select>
          </a-input-group>
        </a-form-item>

        <a-form-item label="鍩熷悕鏁伴噺:">
          <a-input-group compact style="display: flex; width: 230px;">
            <a-input v-model:value="searchForm.domain_count" placeholder="璇疯緭鍏ユ暟閲? style="flex: 1;" @pressEnter="onSearch">
              <template #suffix><search-outlined @click="onSearch" style="color: var(--arl-text-color); opacity: 0.25; cursor: pointer;"/></template>
            </a-input>
            <a-select v-model:value="searchForm.domain_operator" style="width: 75px;">
              <a-select-option value="=">绛変簬</a-select-option>
              <a-select-option value=">">澶т簬</a-select-option>
              <a-select-option value="<">灏忎簬</a-select-option>
            </a-select>
          </a-input-group>
        </a-form-item>

        <a-form-item label="WIH鏁伴噺:">
          <a-input-group compact style="display: flex; width: 230px;">
            <a-input v-model:value="searchForm.wih_count" placeholder="璇疯緭鍏ユ暟閲? style="flex: 1;" @pressEnter="onSearch">
              <template #suffix><search-outlined @click="onSearch" style="color: var(--arl-text-color); opacity: 0.25; cursor: pointer;"/></template>
            </a-input>
            <a-select v-model:value="searchForm.wih_operator" style="width: 75px;">
              <a-select-option value="=">绛変簬</a-select-option>
              <a-select-option value=">">澶т簬</a-select-option>
              <a-select-option value="<">灏忎簬</a-select-option>
            </a-select>
          </a-input-group>
        </a-form-item>

      </a-form>
    </div>

    <div style="margin-bottom: 16px;">
      <a-button :disabled="!hasSelected" style="margin-right: 8px;" @click="handleBatchDelete">鎵归噺鍒犻櫎</a-button>
      <a-button :disabled="!hasSelected" style="margin-right: 8px;" @click="handleBatchStop">鎵归噺鍋滄</a-button>
      <a-dropdown :disabled="!hasSelected">
        <template #overlay>
          <a-menu @click="handleBatchExport">
            <a-menu-item key="cip">C娈?鎵归噺瀵煎嚭</a-menu-item>
            <a-menu-item key="domain">鍩熷悕鎵归噺瀵煎嚭</a-menu-item>
            <a-menu-item key="ip">IP 鎵归噺瀵煎嚭</a-menu-item>
            <a-menu-item key="ip_port">IP 绔彛鎵归噺瀵煎嚭</a-menu-item>
            <a-menu-item key="site">绔欑偣鎵归噺瀵煎嚭</a-menu-item>
            <a-menu-item key="url">URL鎵归噺瀵煎嚭</a-menu-item>
            <a-menu-item key="wih">WIH鎵归噺瀵煎嚭</a-menu-item>
          </a-menu>
        </template>
        <a-button>鎵归噺瀵煎嚭 <down-outlined /></a-button>
      </a-dropdown>
    </div>

    <a-table
        :row-selection="{ selectedRowKeys: selectedRowKeys, onChange: onSelectChange }"
        :dataSource="taskList"
        :columns="columns"
        :loading="loading"
        :pagination="false"
        :scroll="{ x: 'max-content' }"
        :rowKey="(record) => record.task_id || record._id"
        bordered
        style="margin-bottom: 16px;"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'name'">
          <a style="font-weight: 500;" @click="viewTask(record)">{{ record.name }}</a>
        </template>

        <template v-else-if="column.key === 'target'">
          <a-tooltip placement="topLeft">
            <template #title>
              <div style="word-break: break-all; max-height: 300px; overflow-y: auto;">
                <div v-for="(item, index) in (Array.isArray(record.target) ? record.target : String(record.target).split(/[,\s]+/)).filter(Boolean)" :key="index">
                  {{ item.trim() }}
                </div>
              </div>
            </template>
            <div style="max-width: 250px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
              {{ record.target }}
            </div>
          </a-tooltip>
        </template>

        <template v-else-if="column.key === 'statistic'">
          <div v-if="record.statistic" style="display: flex; gap: 8px; flex-wrap: wrap;">
            <a-badge v-if="record.statistic.site_cnt !== undefined" :count="record.statistic.site_cnt" title="绔欑偣" />
            <a-badge v-if="record.statistic.domain_cnt !== undefined" :count="record.statistic.domain_cnt" title="鍩熷悕" />
            <a-badge v-if="record.statistic.ip_cnt !== undefined" :count="record.statistic.ip_cnt" :number-style="{ backgroundColor: '#52c41a' }" title="IP" />
          </div>
          <span v-else style="color: var(--arl-text-color); opacity: 0.45;">-</span>
        </template>

        <template v-else-if="column.key === 'options'">
          <a-tooltip placement="bottom" color="var(--arl-text-color)">
            <template #title>
              <div v-for="(item, index) in getDetailedOptions(record.options)" :key="index" style="line-height: 2;">
                {{ item }}
              </div>
            </template>
            <div style="max-width: 180px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer;">
              {{ formatOptions(record.options) }}
            </div>
          </a-tooltip>
        </template>

        <template v-else-if="column.key === 'status'">
          <a-tooltip v-if="record.service && record.service.length > 0" placement="bottom" color="var(--arl-text-color)">
            <template #title>
              <div v-for="(item, index) in record.service" :key="index" style="line-height: 2; font-size: 13px;">
                {{ item.name }}: {{ item.elapsed }}
              </div>
            </template>
            <div style="display: inline-block; cursor: pointer;">
              <a-tag :color="getStatusColor(record.status)" style="margin-right: 0;">{{ record.status }}</a-tag>
            </div>
          </a-tooltip>

          <a-tag v-else :color="getStatusColor(record.status)">{{ record.status }}</a-tag>
        </template>

        <template v-else-if="column.key === 'task_id'">
          <a @click="viewTask(record)">{{ record._id }}</a>
        </template>

        <template v-else-if="column.key === 'action'">
          <a-space size="small">
            <a-button type="link" size="small" style="color: var(--arl-text-color); padding: 0 4px;" @click="syncTask(record)">鍚?姝?/a-button>
            <a-button type="link" size="small" style="color: var(--arl-text-color); padding: 0 4px;" @click="exportTask(record)">瀵?鍑?/a-button>

            <a-button type="link" size="small" style="color: var(--arl-text-color); padding: 0 4px;" @click="stopSingleTask(record)" :disabled="record.status === 'done' || record.status === 'error'">鍋?姝?/a-button>

            <a-button type="link" size="small" style="color: var(--arl-text-color); padding: 0 4px;" :disabled="record.status !== 'done' && record.status !== 'error'" @click="deleteSingleTask(record)">鍒?闄?/a-button>

            <a-button type="link" size="small" style="color: var(--arl-text-color); padding: 0 4px;" @click="restartTask(record)">閲?鍚?/a-button>
          </a-space>
        </template>

      </template>
    </a-table>

    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 16px;">
      <div style="color: var(--arl-text-color); opacity: 0.65;">鍏?{{ Math.ceil(pagination.total / pagination.pageSize) || 1 }} 椤?/ {{ pagination.total }} 鏉℃暟鎹?/div>
      <a-pagination v-model:current="pagination.current" v-model:pageSize="pagination.pageSize" :total="pagination.total" show-size-changer @change="handleTableChange" @showSizeChange="handleTableChange" />
    </div>

  </div>

  <a-modal
      v-model:open="visible"
      title="娣诲姞浠诲姟"
      @ok="handleOk"
      :confirmLoading="submitLoading"
      width="560px"
      wrapClassName="arl-theme-modal"
      rootClassName="arl-theme-modal"
      okText="纭?瀹?
      cancelText="鍙?娑?
      :bodyStyle="{ padding: '24px 32px' }"
  >
    <a-form
        ref="formRef"
        :model="formState"
        :label-col="{ style: { width: '115px' } }"
        :wrapper-col="{ style: { width: 'calc(100% - 115px)' } }"
    >
      <a-form-item label="浠诲姟鍚嶇О" name="name" :rules="[{ required: true, message: '璇疯緭鍏ヤ换鍔″悕绉? }]">
        <a-input v-model:value="formState.name" placeholder="璇疯緭鍏ヤ换鍔″悕绉? />
      </a-form-item>

      <a-form-item label="鐩爣" name="target" :rules="[{ required: true, message: '璇疯緭鍏ョ洰鏍? }]">
        <a-textarea
            v-model:value="formState.target"
            placeholder="璇疯緭鍏ョ洰鏍囷紝鏀寔IP銆両P娈点€佸煙鍚?
            :rows="2"
            style="resize: none;"
        />
      </a-form-item>

      <a-form-item label="鍩熷悕鐖嗙牬绫诲瀷" name="domain_brute_type" :rules="[{ required: true }]">
        <a-select v-model:value="formState.domain_brute_type">
          <a-select-option value="test">娴嬭瘯</a-select-option>
          <a-select-option value="big">澶у瓧鍏?/a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="绔彛鎵弿绫诲瀷" name="port_scan_type" :rules="[{ required: true }]">
        <a-select v-model:value="formState.port_scan_type">
          <a-select-option value="test">娴嬭瘯</a-select-option>
          <a-select-option value="top100">TOP100</a-select-option>
          <a-select-option value="top1000">TOP1000</a-select-option>
          <a-select-option value="all">鍏ㄧ鍙?/a-select-option>
          <a-select-option value="custom">鑷畾涔夌鍙ｅ瓧鍏?/a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item :wrapper-col="{ offset: 3, span: 21 }" style="margin-top: 16px; margin-bottom: 0;">
        <div v-for="(category, catIndex) in pluginCategories" :key="catIndex" style="margin-bottom: 16px;">
          <div style="font-size: 14px; font-weight: 500; color: var(--arl-text-color); margin-bottom: 8px;">{{ category.title }}</div>
          <a-row :gutter="[16, 12]">
            <a-col :span="12" v-for="item in category.plugins" :key="item.key">
              <a-checkbox v-model:checked="formState[item.key]">
                <span style="color: var(--arl-text-color); font-size: 13px;">{{ item.label }}</span>
              </a-checkbox>
            </a-col>
          </a-row>
        </div>
      </a-form-item>
    </a-form>
  </a-modal>

  <a-modal
      v-model:open="syncVisible"
      title="鍚屾浠诲姟"
      @ok="handleSyncOk"
      :confirmLoading="syncLoading"
      width="520px"
      wrapClassName="arl-theme-modal"
      rootClassName="arl-theme-modal"
      okText="纭?瀹?
      cancelText="鍙?娑?
  >
    <a-form :model="syncFormState" :label-col="{ span: 5 }" :wrapper-col="{ span: 18 }" style="margin-top: 20px;">
      <a-form-item label="璧勪骇淇℃伅" name="scope_id" :rules="[{ required: true }]">
        <a-select
            v-model:value="syncFormState.scope_id"
            placeholder="璇烽€夋嫨璧勪骇"
            :options="syncOptions"
            allowClear
        >
          <template #notFoundContent>
            <div style="text-align: center; padding: 20px 0;">
              <img src="https://gw.alipayobjects.com/zos/antfincdn/ZHrcdLPrvN/empty.svg" style="height: 35px; opacity: 0.5;" />
              <p style="color: var(--arl-text-color); opacity: 0.45; margin-top: 8px;">鏆傛棤鏁版嵁</p>
            </div>
          </template>
        </a-select>
      </a-form-item>
    </a-form>
  </a-modal>

<!--fofa浠诲姟涓嬪彂寮圭獥-->
  <a-modal
      v-model:open="fofaVisible"
      title="FOFA 浠诲姟涓嬪彂"
      @ok="submitFofaTask"
      :confirmLoading="fofaSubmitLoading"
      width="560px"
      wrapClassName="arl-theme-modal"
      rootClassName="arl-theme-modal"
      okText="纭?瀹?
      cancelText="鍙?娑?
      :bodyStyle="{ padding: '24px 32px' }"
  >
    <a-form
        ref="fofaFormRef"
        :model="fofaForm"
        :label-col="{ style: { width: '90px' } }"
        :wrapper-col="{ style: { width: 'calc(100% - 90px)' } }"
    >
      <a-form-item label="浠诲姟鍚嶇О" name="name" :rules="[{ required: true, message: '璇疯緭鍏ヤ换鍔″悕绉? }]">
        <a-input v-model:value="fofaForm.name" placeholder="璇疯緭鍏ヤ换鍔″悕绉? />
      </a-form-item>

      <a-form-item label="鏌ヨ璇彞" name="query" :rules="[{ required: true, message: '璇疯緭鍏ユ煡璇㈣鍙? }]">
        <div style="display: flex; gap: 12px; align-items: flex-start;">
          <a-input v-model:value="fofaForm.query" placeholder="璇疯緭鍏?FOFA 鏌ヨ璇彞" style="flex: 1;" />
          <a-button type="primary" @click="testFofaQuery" :loading="fofaTestLoading">娴?璇?/a-button>
        </div>
        <div style="margin-top: 8px; color: var(--arl-text-color); margin-left: 4px;">
          缁撴灉鏁帮細{{ fofaResultCount }}
        </div>
      </a-form-item>

      <a-form-item label="鍏宠仈绛栫暐" name="policy_id">
        <a-select
            v-model:value="fofaForm.policy_id"
            placeholder="璇烽€夋嫨鍏宠仈绛栫暐 (鍙€?"
            :options="policyOptions"
            allowClear
        />
      </a-form-item>
    </a-form>
  </a-modal>


</template>

<script setup>
import { ref, reactive, onMounted, computed, createVNode } from 'vue';
import { Modal, message, Checkbox } from 'ant-design-vue';
import { useRouter } from 'vue-router'; // 鏂板锛氬紩鍏ヨ矾鐢遍挬瀛?
// 寮曞叆 Antd 鐨勫浘鏍囷紙鎼滅储鏀惧ぇ闀溿€佷笅鎷夌澶达級
import { SearchOutlined, DownOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue';
import request from '../utils/request';

// --- 琛ㄦ牸涓庢暟鎹€昏緫 ---
const router = useRouter();
const taskList = ref([]);
const loading = ref(false);
const pagination = reactive({ current: 1, pageSize: 10, total: 0, showSizeChanger: true });

// 1:1 杩樺師鍘熺増绮剧‘鐨勫甯﹀垎閰嶏紝骞朵负浠诲姟鍚嶅拰鐩爣寮€鍚帓搴?
const columns = [
  { title: '浠诲姟鍚?, dataIndex: 'name', key: 'name', width: 180, sorter: true, ellipsis: true },
  { title: '鐩爣', dataIndex: 'target', key: 'target', width: 220, sorter: true, ellipsis: true },
  { title: '缁熻', dataIndex: 'statistic', key: 'statistic', width: 100 },
  { title: '閰嶇疆椤?, dataIndex: 'options', key: 'options', width: 160, ellipsis: true },
  { title: '鐘舵€?, dataIndex: 'status', key: 'status', width: 100 },
  { title: '寮€濮嬫椂闂?, dataIndex: 'start_time', key: 'start_time', width: 160 },
  { title: '缁撴潫鏃堕棿', dataIndex: 'end_time', key: 'end_time', width: 160 },
  { title: 'Task_Id', dataIndex: '_id', key: 'task_id', width: 220 },
  { title: '鎿嶄綔', key: 'action', fixed: 'right', width: 280 },
];

// 鍗囩骇鐗堬細鏅鸿兘璇嗗埆 ARL 鐨勫悇绉嶅姩鎬佽繍琛岀姸鎬?
const getStatusColor = (status) => {
  if (status === 'done') return 'success';     // 鎴愬姛锛氱豢鑹?
  if (status === 'error') return 'error';      // 澶辫触锛氱孩鑹?
  if (status === 'waiting') return 'default';  // 绛夊緟锛氱伆鑹?

  // ARL 浼氭妸褰撳墠鎵ц鐨勬彃浠跺悕浣滀负鐘舵€侊紝姣斿 domain_brute, port_scan
  // 鍙涓嶆槸涓婇潰涓夌锛岀粺缁熻涓烘槸鈥滄鍦ㄨ繍琛屸€濓紝鏄剧ず涓鸿摑鑹插鐞嗕腑鐘舵€?
  return 'processing';
};

// 瑙ｆ瀽 JSON 涓殑 options 瀵硅薄锛岃浆鎹负涓枃閫楀彿鍒嗛殧瀛楃涓?
const formatOptions = (options) => {
  if (!options) return '-';
  const activeOptions = [];
  for (const key in options) {
    if (options[key] === true) {
      // 鍦ㄦ柊鐨?pluginList 涓鎵句腑鏂囨爣绛?
      const plugin = pluginList.find(item => item.key === key);
      if (plugin) {
        activeOptions.push(plugin.label);
      }
    }
  }
  return activeOptions.length > 0 ? activeOptions.join(', ') : '-';
};
// 馃毃 鏂板锛氫笓闂ㄧ粰榛戣壊 Tooltip 姘旀场鐢ㄧ殑楂樼骇瑙ｆ瀽鍑芥暟 (鏀寔鎹㈣鍜屾彁鍙栧瓙绫诲瀷)
const getDetailedOptions = (options) => {
  if (!options) return ['-'];
  const detailed = [];

  // 1. 鎻愬彇鏅€氱殑甯冨皵鍊兼彃浠?(涓?true 鐨勯」)
  for (const key in options) {
    if (options[key] === true) {
      const plugin = pluginList.find(item => item.key === key);
      if (plugin) detailed.push(plugin.label);
    }
  }

  // 2. 鎻愬彇骞剁炕璇戠壒娈婄殑鍏蜂綋閰嶇疆椤?(濡傚瓧鍏哥被鍨嬨€佺鍙ｈ寖鍥?
  if (options.domain_brute_type) {
    const typeMap = { test: '娴嬭瘯', big: '澶у瓧鍏? };
    detailed.push(`鍩熷悕鐖嗙牬绫诲瀷: ${typeMap[options.domain_brute_type] || options.domain_brute_type}`);
  }
  if (options.port_scan_type) {
    const typeMap = { test: '娴嬭瘯', top100: 'TOP100', top1000: 'TOP1000', all: '鍏ㄧ鍙? };
    // 蹇界暐 null 鍊?
    if(options.port_scan_type !== 'null' && options.port_scan_type !== null) {
      detailed.push(`绔彛鎵弿绫诲瀷: ${typeMap[options.port_scan_type] || options.port_scan_type.toUpperCase()}`);
    }
  }

  return detailed.length > 0 ? detailed : ['-'];
};

// --- 鎼滅储琛ㄥ崟閫昏緫 ---
const searchForm = reactive({
  name: '', target: '', task_id: '', type: undefined,
  status: '', site_count: '', site_operator: '=',
  domain_count: '', domain_operator: '=', wih_count: '', wih_operator: '='
});

// --- 琛ㄦ牸澶氶€夐€昏緫 ---
const selectedRowKeys = ref([]);
const hasSelected = computed(() => selectedRowKeys.value.length > 0);
const onSelectChange = (keys) => {
  selectedRowKeys.value = keys;
};



// 馃挜 瀹岀編澶嶅埢 ARL 浠诲姟鍒犻櫎锛氭敮鎸佸姩鎬佸嬀閫夋槸鍚﹀垹闄ゅ簳灞傛暟鎹?
const handleBatchDelete = () => {
  if (!hasSelected.value) {
    message.warning('璇峰厛鍕鹃€夐渶瑕佸垹闄ょ殑浠诲姟');
    return;
  }

  // 1. 鏁版嵁娑堟潃锛岀‘淇濇嬁鍒扮殑鏄函鍑€鐨?ID 鏁扮粍
  const validKeys = selectedRowKeys.value.filter(key => key != null);

  if (validKeys.length === 0) {
    message.error('鑾峰彇浠诲姟ID澶辫触锛岃妫€鏌ヨ〃鏍?rowKey 璁剧疆锛?);
    return;
  }

  // 2. 瀹氫箟灞€閮ㄥ彉閲忔帴绠″閫夋鐨勭姸鎬侊紙榛樿鎵撳嬀锛屽榻?ARL 鍘熺増閫昏緫锛?
  let isDeleteData = true;

  Modal.confirm({
    title: '鍒犻櫎纭',
    icon: createVNode(ExclamationCircleOutlined),
    // 3. 鍒╃敤 createVNode 鍔ㄦ€佹覆鏌撲竴娈靛寘鍚?Checkbox 鐨勬彁绀哄唴瀹?
    content: createVNode('div', { style: 'margin-top: 8px;' }, [
      createVNode('div', { style: 'margin-bottom: 16px; color: var(--arl-text-color);' }, `纭瑕佸垹闄ら€変腑鐨?${validKeys.length} 椤逛换鍔″悧锛焋),
      createVNode(Checkbox, {
        defaultChecked: isDeleteData,
        onChange: (e) => { isDeleteData = e.target.checked; } // 鐩戝惉鍕鹃€夌姸鎬佸彉鍖?
      }, () => '鍚屾椂鍒犻櫎璇ヤ换鍔″叧鑱旂殑鎵€鏈夎祫浜ф暟鎹?(涓嶅彲鎭㈠)')
    ]),
    okText: '纭?瀹?,
    cancelText: '鍙?娑?,
    okButtonProps: { danger: true }, // 鍒犻櫎鎸夐挳鏍囩孩锛岀鍚堝畨鍏ㄦ搷浣滆鑼?
    onOk: async () => {
      try {
        // 4. 瀹屽叏瀵归綈浣犳姄鍖呯殑 Payload 缁撴瀯
        const res = await request.post('/task/delete/', {
          del_task_data: isDeleteData, // 璇诲彇鐢ㄦ埛鐨勫嬀閫夌姸鎬?
          task_id: validKeys           // 鍙戦€佽鍕鹃€夌殑浠诲姟 ID 鏁扮粍
        });

        if (res.code === 200) {
          message.success(`鎴愬姛鍒犻櫎 ${validKeys.length} 椤逛换鍔★紒`);
          selectedRowKeys.value = []; // 娓呯┖琛ㄦ牸鍕鹃€夌姸鎬?
          fetchTasks(1, pagination.pageSize); // 鍒锋柊琛ㄦ牸骞跺洖鍒扮涓€椤?
        } else {
          message.error('鍒犻櫎澶辫触: ' + (res.message || '鏈煡閿欒'));
        }
      } catch (error) {
        console.error('鎵归噺鍒犻櫎浠诲姟寮傚父:', error);
        message.error('缃戠粶寮傚父锛岃鏌ョ湅鎺у埗鍙?);
      }
    }
  });
};

// 馃挜 瀹岀編澶嶅埢 ARL 浠诲姟鍋滄锛氭壒閲忓己鍒剁粓姝㈤€変腑鐨勪换鍔?
const handleBatchStop = () => {
  if (!hasSelected.value) {
    message.warning('璇峰厛鍕鹃€夐渶瑕佸仠姝㈢殑浠诲姟');
    return;
  }

  // 1. 鏁版嵁娑堟潃锛岀‘淇濇嬁鍒扮殑鏄函鍑€鐨?ID 鏁扮粍
  const validKeys = selectedRowKeys.value.filter(key => key != null);

  if (validKeys.length === 0) {
    message.error('鑾峰彇浠诲姟ID澶辫触锛岃妫€鏌ヨ〃鏍?rowKey 璁剧疆锛?);
    return;
  }

  // 2. 鍘熺増椋庢牸鐨勭‘璁ゅ脊绐楋紙涓嶉渶瑕佸唴閮ㄥ閫夋浜嗭級
  Modal.confirm({
    title: '鍋滄纭',
    icon: createVNode(ExclamationCircleOutlined),
    content: `纭瑕佸己鍒跺仠姝㈤€変腑鐨?${validKeys.length} 椤逛换鍔″悧锛焋,
    okText: '纭?瀹?,
    cancelText: '鍙?娑?,
    // 鍋滄鎸夐挳涓嶉渶瑕佸儚鍒犻櫎閭ｆ牱鏍囩孩锛屼繚鎸侀粯璁ょ殑钃濊壊鍗冲彲
    onOk: async () => {
      try {
        // 3. 1:1 瀵归綈浣犳姄鍖呯殑鏋佺畝 Payload 缁撴瀯
        const res = await request.post('/task/batch_stop/', {
          task_id: validKeys
        });

        if (res.code === 200) {
          message.success(`鎴愬姛涓嬪彂鍋滄鎸囦护缁?${validKeys.length} 椤逛换鍔★紒`);
          selectedRowKeys.value = []; // 娓呯┖琛ㄦ牸鍕鹃€夌姸鎬?
          fetchTasks(pagination.current, pagination.pageSize); // 鍒锋柊褰撳墠椤佃〃鏍间互鑾峰彇鏈€鏂扮姸鎬?
        } else {
          message.error('鍋滄澶辫触: ' + (res.message || '鏈煡閿欒'));
        }
      } catch (error) {
        console.error('鎵归噺鍋滄浠诲姟寮傚父:', error);
        message.error('缃戠粶寮傚父锛岃鏌ョ湅鎺у埗鍙?);
      }
    }
  });
};

// 馃挜 瀹岀編澶嶅埢 ARL 浠诲姟鎵归噺瀵煎嚭锛氭敮鎸佺函鏂囨湰鏂囦欢娴佽嚜鍔ㄤ笅杞?
const handleBatchExport = async ({ key }) => {
  if (!hasSelected.value) {
    message.warning('璇峰厛鍕鹃€夐渶瑕佸鍑虹殑浠诲姟');
    return;
  }

  const validKeys = selectedRowKeys.value.filter(k => k != null);
  if (validKeys.length === 0) {
    message.error('鑾峰彇浠诲姟ID澶辫触锛岃妫€鏌ヨ〃鏍?rowKey 璁剧疆锛?);
    return;
  }

  try {
    // 寮瑰嚭涓€涓姞杞芥彁绀猴紝闃叉鐢ㄦ埛鍦ㄤ笅杞藉ぇ鏂囦欢鏃剁柉鐙傜偣鍑?
    message.loading({ content: '姝ｅ湪鐢熸垚瀵煎嚭鏂囦欢...', key: 'exporting' });

    // 鍙戣捣 POST 璇锋眰銆?
    // 馃毃 鏍稿績璁惧畾锛氬姞涓?responseType: 'blob'锛屽己鍒惰 Axios 鎶婅繑鍥炵殑绾枃鏈?鏂囦欢娴佸綋浣?Blob 瀵硅薄澶勭悊锛?
    // 閬垮厤浣犱滑椤圭洰涓殑 request 鎷︽埅鍣ㄨ瘯鍥炬妸瀹冨綋浣?JSON (res.code === 200) 鏉ヨВ鏋愪粠鑰屽紩鍙戞姤閿欍€?
    const res = await request.post(`/batch_export/${key}/`, {
      task_id: validKeys
    }, {
      responseType: 'blob'
    });

    // 鍒涘缓铏氭嫙鏂囦欢瀵硅薄 (Blob)
    const blob = new Blob([res], { type: 'text/plain;charset=utf-8' });
    const downloadUrl = window.URL.createObjectURL(blob);

    // 鍒涘缓涓€涓殣钘忕殑 <a> 鏍囩骞舵ā鎷熺偣鍑讳笅杞?
    const link = document.createElement('a');
    link.href = downloadUrl;
    // 鍔ㄦ€佺敓鎴愭枃浠跺悕锛屼緥濡傦細batch_export_cip.txt
    link.download = `batch_export_${key}.txt`;
    document.body.appendChild(link);
    link.click();

    // 涓嬭浇瀹屾瘯鍚庢竻鐞?DOM 鍜屽唴瀛樹腑鐨勪复鏃?URL
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);

    // 鏇存柊鍔犺浇鎻愮ず涓烘垚鍔熺姸鎬?
    message.success({ content: '瀵煎嚭鎴愬姛锛?, key: 'exporting', duration: 2 });

  } catch (error) {
    console.error('鎵归噺瀵煎嚭寮傚父:', error);
    message.error({ content: '瀵煎嚭澶辫触锛岃鏌ョ湅鎺у埗鍙?, key: 'exporting', duration: 2 });
  }
};

// 鐐瑰嚮鍚屾寮圭獥鈥滅‘瀹氣€濇寜閽?
const handleSyncOk = async () => {
  if (!syncFormState.scope_id) {
    message.warning('璇烽€夋嫨璧勪骇淇℃伅');
    return;
  }

  syncLoading.value = true;
  try {
    // 1:1 瀵归綈鎶撳寘锛歅OST /api/task/sync/
    // Payload 缁撴瀯锛歿"scope_id": "...", "task_id": "..."}
    const res = await request.post('/task/sync/', {
      scope_id: syncFormState.scope_id,
      task_id: currentSyncRecord.value._id || currentSyncRecord.value.task_id
    });

    if (res.code === 200) {
      message.success('鍚屾浠诲姟涓嬪彂鎴愬姛 馃殌');
      syncVisible.value = false;
      // 鍒锋柊鍒楄〃浠ユ樉绀烘渶鏂扮姸鎬?
      fetchTasks(pagination.current, pagination.pageSize);
    } else {
      message.error('鍚屾澶辫触: ' + (res.message || '鏈煡閿欒'));
    }
  } catch (error) {
    console.error('鍚屾璇锋眰寮傚父:', error);
    message.error('缃戠粶寮傚父锛岃绋嶅悗鍐嶈瘯');
  } finally {
    syncLoading.value = false;
  }
};

// --- 鏁版嵁鑾峰彇 ---
// --- 鏁版嵁鑾峰彇涓庢悳绱㈤€昏緫 ---
// --- 鏁版嵁鑾峰彇涓庢悳绱㈤€昏緫 ---
const fetchTasks = async (page = 1, size = 10) => {
  loading.value = true;
  try {
    // 1. 鍩虹鍒嗛〉鍙傛暟
    const queryParams = { page, size };

    // 2. 鏄犲皠鍩虹鏂囨湰妗?(绮惧噯鎺掔┖)
    if (searchForm.name) queryParams.name = searchForm.name;
    if (searchForm.target) queryParams.target = searchForm.target;
    if (searchForm.status) queryParams.status = searchForm.status;

    // 3. 馃毃 淇 Task_Id: 鏄犲皠涓?_id
    if (searchForm.task_id) queryParams._id = searchForm.task_id;

    // 4. 馃毃 淇 浠诲姟绫诲瀷: 鏄犲皠涓?task_tag
    if (searchForm.type) queryParams.task_tag = searchForm.type;

    // 5. 馃毃 淇 鏁伴噺缁熻: 灏佽涓哄悗绔璇嗙殑 statistic.xxx 鏍煎紡
    const appendCountParam = (count, operator, baseKey) => {
      if (count !== '' && count !== null && count !== undefined) {
        if (operator === '=') {
          queryParams[baseKey] = count;
        } else if (operator === '>') {
          queryParams[`${baseKey}_gt`] = count; // ARL 鐨勫ぇ浜庤娉?
        } else if (operator === '<') {
          queryParams[`${baseKey}_lt`] = count; // ARL 鐨勫皬浜庤娉?
        }
      }
    };

    // 渚濇灏嗗墠绔粦瀹氱殑鍙屽彉閲忚浆鎹负鍚庣璁よ瘑鐨勫崟 key
    appendCountParam(searchForm.site_count, searchForm.site_operator, 'statistic.site_cnt');
    appendCountParam(searchForm.domain_count, searchForm.domain_operator, 'statistic.domain_cnt');
    appendCountParam(searchForm.wih_count, searchForm.wih_operator, 'statistic.wih_cnt');

    // 鍙戦€佹渶缁堟嫾瑁呭ソ鐨勭粷璧炲弬鏁?
    const res = await request.get('/task/', { params: queryParams });

    if (res.code === 200) {
      taskList.value = res.items || [];
      pagination.total = res.total || 0;
      pagination.current = page;
      pagination.pageSize = size;
    } else {
      console.error('鑾峰彇鍒楄〃澶辫触:', res);
    }
  } catch (error) {
    console.error('API 璇锋眰澶辫触:', error);
  } finally {
    loading.value = false;
  }
};

// 瑙﹀彂鎼滅储鐨勬嵎寰勬柟娉曪紙寮哄埗鍥炲埌绗竴椤碉級
const onSearch = () => {
  fetchTasks(1, pagination.pageSize);
};

const handleTableChange = (page, pageSize) => fetchTasks(page, pageSize);
onMounted(() => fetchTasks(pagination.current, pagination.pageSize));

// --- 寮圭獥閫昏緫 (淇濇寔鍘熸牱) ---
const visible = ref(false);
const submitLoading = ref(false);
const formRef = ref();

// === 1. 缁撴瀯鍖栫殑鎻掍欢鍒嗙被鏁版嵁妯″瀷 ===
const pluginCategories = [
  {
    title: '馃寪 鍩虹璧勪骇渚︽煡',
    plugins: [
      { key: 'dns_query_plugin', label: '鍩熷悕鏌ヨ鎻掍欢' },
      { key: 'domain_brute', label: '鍩熷悕鐖嗙牬' },
      { key: 'alt_dns', label: 'DNS瀛楀吀鏅鸿兘鐢熸垚' },
      { key: 'arl_search', label: 'ARL 鍘嗗彶鏌ヨ' }
    ]
  },
  {
    title: '鈿★笍 绔彛涓庢湇鍔″彂鐜?,
    plugins: [
      { key: 'skip_scan_cdn_ip', label: '璺宠繃CDN' },
      { key: 'port_scan', label: '绔彛鎵弿' },
      { key: 'service_detection', label: '鏈嶅姟璇嗗埆' },
      { key: 'os_detection', label: '鎿嶄綔绯荤粺璇嗗埆' },
      { key: 'ssl_cert', label: 'SSL 璇佷功鑾峰彇' }
    ]
  },
  {
    title: '馃暦锔?Web 娣卞害鎺㈡祴',
    plugins: [
      { key: 'site_identify', label: '绔欑偣璇嗗埆' },
      { key: 'search_engines', label: '鎼滅储寮曟搸璋冪敤' },
      { key: 'site_spider', label: '绔欑偣鐖櫕' },
      { key: 'web_info_hunter', label: 'WIH 璋冪敤' },
      { key: 'file_leak', label: '鏂囦欢娉勯湶' },
      { key: 'findvhost', label: 'Host 纰版挒' },
      { key: 'npoc_service_detection', label: '鏈嶅姟(python)璇嗗埆' },
      { key: 'nuclei_scan', label: 'nuclei 璋冪敤' },
      { key: 'js_analysis', label: 'JS 娣卞害鍒嗘瀽' }
    ]
  },
  {
    title: '馃攧 寰幆鏀舵暃锛堥粯璁ゅ叧闂級',
    plugins: [
      { key: 'convergence_enabled', label: '鍚敤鏀舵暃' }
    ]
  }
];

// 涓轰簡鍏煎鍘熸湁鏁版嵁缁撴瀯锛屽埄鐢?flatMap 鍔ㄦ€佽绠楀嚭鎵佸钩鐨?pluginList
const pluginList = pluginCategories.flatMap(cat => cat.plugins);

// === 2. 鍖归厤鎴浘鐨勯粯璁ゅ嬀閫夌姸鎬?===
const defaultPlugins = {
  domain_brute: true, alt_dns: true, dns_query_plugin: true, arl_search: true,
  port_scan: true, service_detection: false, os_detection: false, ssl_cert: false,
  skip_scan_cdn_ip: true, site_identify: false, search_engines: false, site_spider: false,
  file_leak: false, findvhost: false, nuclei_scan: false, web_info_hunter: false,
  npoc_service_detection: false, js_analysis: false,
  convergence_enabled: false,
  convergence_max_rounds: 3,
  convergence_min_new: 5,
  convergence_ratio: "0.05"
};

// === 3. 琛ㄥ崟鐘舵€佸垵濮嬪寲锛堜笉鍐嶄緷璧栦换浣曞簾寮冨彉閲忥級 ===
const formState = reactive({
  name: "",
  target: "",
  domain_brute_type: "big",
  port_scan_type: "TOP100",
  ...defaultPlugins
});

const showModal = () => { visible.value = true; };

// 璺宠浆鍒拌鎯呴〉锛屽苟鎶婂叏閮ㄧ粺璁℃暟鎹杩?URL
// --- 鎿嶄綔鍒楅€昏緫 ---
const viewTask = (record) => {
  // 1. 闃插尽鎬ф鏌ワ細纭繚浼犲叆鐨勭‘瀹炴槸涓€琛屾暟鎹璞?
  if (!record || !record._id) {
    console.error('viewTask 鎺ユ敹鍒扮殑鍙傛暟鏈夎:', record);
    return;
  }

  // 2. 鎷艰鍩虹鏌ヨ鍙傛暟
  const query = {
    task_id: record._id,
    targetName: record.target
  };

  // 3. 鎶婄粺璁℃暟鎹噷鐨勬暟閲忎篃鍏ㄩ儴瑙ｆ瀯杩涘幓 (閫傞厤 ARL 鍘熺増鐨?url 浼犲弬褰㈠紡)
  if (record.statistic) {
    Object.assign(query, record.statistic);
  }

  // 4. 鎵ц璺宠浆锛?
  console.log('鍑嗗璺宠浆鍒拌鎯呴〉锛屾惡甯﹀弬鏁?', query);
  router.push({ path: '/taskList/taskDetail', query });
};




// === 鍚屾浠诲姟涓撳睘鐘舵€?===
const syncVisible = ref(false);
const syncLoading = ref(false);
const syncOptions = ref([]); // 涓嬫媺妗嗚祫浜у垪琛?
const currentSyncRecord = ref(null);
const syncFormState = reactive({
  scope_id: undefined
});





// ==========================================
// 馃挜 浠诲姟绠＄悊锛氬崟琛屾搷浣?5 澶ф牳蹇冨姛鑳?1:1 澶嶅埢
// ==========================================

// 1. 鍚屾 (Sync)
// 鐐瑰嚮琛ㄦ牸鈥滃悓姝モ€濇寜閽殑鎿嶄綔
const syncTask = async (record) => {
  currentSyncRecord.value = record;
  syncFormState.scope_id = undefined;
  syncOptions.value = [];
  syncVisible.value = true;

  try {
    // 1:1 瀵归綈鎶撳寘锛欸ET /api/task/sync_scope/?target=...
    const res = await request.get('/task/sync_scope/', {
      params: { target: record.target }
    });

    if (res.code === 200) {
      // 瀵归綈鎶撳寘 Response锛氭彁鍙?_id 鍜?name
      syncOptions.value = (res.items || []).map(item => ({
        value: item._id,
        label: item.name
      }));
    }
  } catch (error) {
    console.error('鑾峰彇璧勪骇閫夐」澶辫触:', error);
  }
};

// 2. 瀵煎嚭 Excel (Export)
const exportTask = async (record) => {
  try {
    message.loading({ content: '姝ｅ湪鐢熸垚 Excel 瀵煎嚭鏂囦欢...', key: 'exporting_excel' });

    // 瀵归綈 Payload: /api/export/{task_id}
    // 馃毃 蹇呴』鍔?responseType: 'blob'锛屽惁鍒?Axios 鎷垮埌 Excel 鐨勪簩杩涘埗涔辩爜浼氭姤閿欏穿婧?
    const res = await request.get(`/export/${record._id || record.task_id}`, {
      responseType: 'blob'
    });

    // 灏嗕簩杩涘埗娴佺粍瑁呬负 .xlsx Excel 鏂囦欢
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const downloadUrl = window.URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `ARL_Task_${record.name}_Export.xlsx`; // 鍔ㄦ€佹嫾瑁呮洿浼橀泤鐨勬枃浠跺悕
    document.body.appendChild(link);
    link.click();

    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);

    message.success({ content: 'Excel 瀵煎嚭鎴愬姛锛?, key: 'exporting_excel', duration: 2 });
  } catch (error) {
    console.error('瀵煎嚭 Excel 寮傚父:', error);
    message.error({ content: '瀵煎嚭寮傚父锛岃鏌ョ湅鎺у埗鍙?, key: 'exporting_excel', duration: 2 });
  }
};

// 3. 鍋滄鍗曡浠诲姟 (Stop)
const stopSingleTask = async (record) => {
  try {
    // 瀵归綈 Payload: /api/task/stop/{task_id} (鏃?body)
    const res = await request.get(`/task/stop/${record._id || record.task_id}`);
    if (res.code === 200) {
      message.success('宸插彂閫佸仠姝㈡寚浠?馃洃');
      fetchTasks(pagination.current, pagination.pageSize); // 鍒锋柊琛ㄦ牸鐘舵€?
    } else {
      message.error('鍋滄澶辫触: ' + (res.message || '鏈煡閿欒'));
    }
  } catch (error) {
    message.error('缃戠粶寮傚父锛屽仠姝㈠け璐?);
  }
};

// 4. 鍒犻櫎鍗曡浠诲姟 (Delete)
const deleteSingleTask = (record) => {
  let isDeleteData = true;

  Modal.confirm({
    title: '鍒犻櫎纭',
    icon: createVNode(ExclamationCircleOutlined),
    content: createVNode('div', { style: 'margin-top: 8px;' }, [
      createVNode('div', { style: 'margin-bottom: 16px; color: var(--arl-text-color);' }, `纭瑕佸垹闄よ浠诲姟鍚楋紵`),
      createVNode(Checkbox, {
        defaultChecked: isDeleteData,
        onChange: (e) => { isDeleteData = e.target.checked; }
      }, () => '鍚屾椂鍒犻櫎璇ヤ换鍔″叧鑱旂殑鎵€鏈夎祫浜ф暟鎹?(涓嶅彲鎭㈠)')
    ]),
    okText: '纭?瀹?,
    cancelText: '鍙?娑?,
    okButtonProps: { danger: true },
    onOk: async () => {
      try {
        const res = await request.post('/task/delete/', {
          task_id: [record._id || record.task_id],
          del_task_data: isDeleteData
        });

        if (res.code === 200) {
          message.success('浠诲姟鍒犻櫎鎴愬姛');
          fetchTasks(pagination.current, pagination.pageSize);
        } else {
          message.error('鍒犻櫎澶辫触: ' + (res.message || '鏈煡閿欒'));
        }
      } catch (error) {
        message.error('缃戠粶寮傚父锛屽垹闄ゅけ璐?);
      }
    }
  });
};

// 5. 閲嶅惎浠诲姟 (Restart)
const restartTask = async (record) => {
  try {
    // 瀵归綈 Payload: 浼犳暟缁?
    const res = await request.post('/task/restart/', {
      task_id: [record._id || record.task_id]
    });

    if (res.code === 200) {
      message.success('浠诲姟宸查噸鍚紝姝ｅ湪鎵ц... 馃殌');
      fetchTasks(pagination.current, pagination.pageSize); // 鍒锋柊琛ㄦ牸鐪嬪埌鐘舵€佸彉涓?processing
    } else {
      message.error('閲嶅惎澶辫触: ' + (res.message || '鏈煡閿欒'));
    }
  } catch (error) {
    message.error('缃戠粶寮傚父锛岄噸鍚け璐?);
  }
};



const handleOk = async () => {
  try {
    await formRef.value.validate();
    submitLoading.value = true;
    const res = await request.post('/task/', formState);
    if (res.code === 200) {
      message.success('浠诲姟涓嬪彂鎴愬姛锛?);
      visible.value = false;
      fetchTasks(1, pagination.pageSize);
    } else {
      message.error('涓嬪彂澶辫触: ' + (res.message || '鏈煡閿欒'));
    }
  } catch (error) {
    if (!error.errorFields) message.error('缃戠粶寮傚父');
  } finally {
    submitLoading.value = false;
  }
};



// ==========================================
// 馃挜 FOFA 浠诲姟涓嬪彂锛氳幏鍙栫瓥鐣ャ€佹祴璇曡鍙ャ€佹彁浜よ〃鍗?
// ==========================================
const fofaVisible = ref(false);
const fofaSubmitLoading = ref(false);
const fofaTestLoading = ref(false);
const fofaResultCount = ref(0);
const policyOptions = ref([]); // 瀛樻斁涓嬫媺妗嗙瓥鐣ユ暟鎹?
const fofaFormRef = ref();

const fofaForm = reactive({
  name: '',
  query: '',
  policy_id: undefined
});

// 1. 鎵撳紑寮圭獥锛屽苟鎷夊彇绛栫暐鍒楄〃 (瀵归綈 GET /api/policy/)
const openFofaModal = async () => {
  // 閲嶇疆鐘舵€?
  fofaForm.name = '';
  fofaForm.query = '';
  fofaForm.policy_id = undefined;
  fofaResultCount.value = 0;
  if (fofaFormRef.value) fofaFormRef.value.clearValidate();

  fofaVisible.value = true;

  try {
    // 寮哄埗鍒嗛〉鎷夊彇鏈€澶?1000 鏉＄瓥鐣ワ紝淇濊瘉涓嬫媺妗嗘暟鎹畬鏁?
    const res = await request.get('/policy/', { params: { page: 1, size: 1000 } });
    if (res.code === 200) {
      policyOptions.value = (res.items || []).map(item => ({
        value: item._id,
        label: item.name
      }));
    }
  } catch (error) {
    console.error('鎷夊彇鍏宠仈绛栫暐澶辫触:', error);
  }
};

// 2. 鐐瑰嚮鈥滄祴璇曗€濇寜閽?(瀵归綈 POST /api/task_fofa/test)
const testFofaQuery = async () => {
  if (!fofaForm.query) {
    message.warning('璇峰厛杈撳叆鏌ヨ璇彞鍐嶈繘琛屾祴璇?);
    return;
  }

  fofaTestLoading.value = true;
  try {
    const res = await request.post('/task_fofa/test', { query: fofaForm.query });

    // 濡傛灉 FOFA 閰嶇疆姝ｅ父骞惰繑鍥炰簡鏁版嵁 (鍏煎 size 鎴?total 瀛楁)
    if (res.code === 200) {
      fofaResultCount.value = res.data?.size || res.data?.total || 0;
      message.success('娴嬭瘯杩炴帴鎴愬姛');
    } else {
      // 瀹岀編鎷︽埅浣犳姄鍒扮殑 1202 閿欒 (Fofa key is not set)
      fofaResultCount.value = 0;
      message.error(res.message || '娴嬭瘯澶辫触');
    }
  } catch (error) {
    fofaResultCount.value = 0;
    message.error('娴嬭瘯璇锋眰寮傚父锛岃鏌ョ湅鎺у埗鍙?);
  } finally {
    fofaTestLoading.value = false;
  }
};

// 3. 鐐瑰嚮鈥滅‘瀹氣€濅笅鍙戜换鍔?(瀵归綈 POST /api/task_fofa/submit)
const submitFofaTask = async () => {
  try {
    await fofaFormRef.value.validate(); // 瑙﹀彂蹇呭～鏍￠獙

    fofaSubmitLoading.value = true;
    const res = await request.post('/task_fofa/submit', {
      name: fofaForm.name,
      query: fofaForm.query,
      policy_id: fofaForm.policy_id
    });

    if (res.code === 200) {
      message.success('FOFA 浠诲姟涓嬪彂鎴愬姛锛?);
      fofaVisible.value = false;
      fetchTasks(1, pagination.pageSize); // 鍥炲埌绗竴椤靛苟鍒锋柊鍒楄〃
    } else {
      // 瀹岀編鎷︽埅浣犳姄鍒扮殑 1201 閿欒 (please set fofa key in config-docker.yaml)
      message.error(res.message || '浠诲姟涓嬪彂澶辫触');
    }
  } catch (error) {
    if (!error.errorFields) { // 鎺掗櫎琛ㄥ崟鏍￠獙鎶ラ敊
      message.error('缃戠粶璇锋眰寮傚父');
    }
  } finally {
    fofaSubmitLoading.value = false;
  }
};

// 馃挜 鍏ㄥ眬鏌ョ湅锛氳烦杞埌璇︽儏椤碉紝浣嗕笉甯?task_id 鍙傛暟
const goToGlobalView = () => {
  router.push({
    path: '/taskList/taskDetail',
    query: {
      targetName: '鍏ㄥ眬', // 璁╄鎯呴〉鐨勬爣棰樻樉绀轰负鈥滃叏灞€鐩稿叧璧勪骇鈥?
      // 娉ㄦ剰锛氳繖閲屾晠鎰忎笉浼?task_id
    }
  });
};


</script>

<style scoped>
/* ==========================================
   1. 琛ㄥ崟鏍囩鏂囧瓧寰皟 (璐磋繎鍘熺増棰滆壊鍜屽ぇ灏?
========================================== */
:deep(.ant-form-item-label > label) {
  font-size: 14px;
  color: var(--arl-text-color);
}

</style>


<template>
  <a-layout :style="{ minHeight: '100vh', background: 'transparent' }">
    <a-layout-sider v-model:collapsed="collapsed" collapsible :trigger="null" width="170" :style="{ background: hasBgImage ? (isUIHidden ? 'transparent' : 'rgba(11, 17, 32, 0.6)') : '#0b1120', borderRight: isUIHidden ? 'none' : (isDarkMode ? '1px solid #1e293b' : 'none'), transition: 'all 0.5s' }">
      <div class="logo-container" @click="toggleUI" title="点击隐藏/显示界面" style="height: 64px; display: flex; align-items: center; justify-content: center; cursor: pointer; z-index: 999; position: relative;" :style="{ background: hasBgImage ? 'transparent' : '#0b1120', borderBottom: isDarkMode ? '1px solid #1e293b' : 'none' }">
        <DeploymentUnitOutlined class="logo-icon" :style="{ color: 'var(--arl-theme-color)', fontSize: '20px' }" />
        <span class="logo-text" v-show="!collapsed" style="color: #f1f5f9; font-size: 16px; margin-left: 8px; font-weight: 500;">ARL-Next</span>
      </div>

      <a-menu :style="{ opacity: isUIHidden ? 0 : 1, pointerEvents: isUIHidden ? 'none' : 'auto', transition: 'opacity 0.5s' }" v-model:selectedKeys="selectedKeys" theme="dark" mode="inline" @click="handleMenuClick">
        <a-menu-item key="/dashboard"><DashboardOutlined /><span>仪表盘</span></a-menu-item>
        <a-menu-item key="/assetRecon"><SearchOutlined /><span>企业资产查询</span></a-menu-item>
        <a-menu-item key="/group"><AppstoreOutlined /><span>资产分组</span></a-menu-item>
        <a-menu-item key="/taskList"><GlobalOutlined /><span>任务管理</span></a-menu-item>
        <a-menu-item key="/asset-search"><SearchOutlined /><span>资产搜索</span></a-menu-item>
        <a-menu-item key="/assetsMonitor"><DesktopOutlined /><span>资产监控</span></a-menu-item>
        <a-menu-item key="/planningTasks"><ClockCircleOutlined /><span>计划任务</span></a-menu-item>
        <a-menu-item key="/GitHubTasks/GitHubTasksList"><GithubOutlined /><span>GitHub监控</span></a-menu-item>
        <a-menu-item key="/pocList"><BugOutlined /><span>POC管理</span></a-menu-item>
        <a-menu-item key="/fingerprint"><TagsOutlined /><span>指纹管理</span></a-menu-item>
        <a-menu-item key="/policy"><SettingOutlined /><span>策略配置</span></a-menu-item>
        <a-menu-item key="/systemSettings"><SettingOutlined /><span>系统设置</span></a-menu-item>
      </a-menu>
    </a-layout-sider>

    <a-layout :style="{ background: 'transparent', opacity: isUIHidden ? 0 : 1, pointerEvents: isUIHidden ? 'none' : 'auto', transition: 'opacity 0.5s' }">
      <a-layout-header :style="{ background: isDarkMode ? 'rgba(15, 23, 42, 0.75)' : 'rgba(255, 255, 255, 0.75)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid ' + (isDarkMode ? '#1e293b' : '#e2e8f0'), zIndex: 10, position: 'sticky', top: 0 }">
        <div style="display: flex; align-items: center;">
          <span class="trigger" @click="() => (collapsed = !collapsed)" style="font-size: 18px; cursor: pointer; margin-right: 24px;">
            <menu-unfold-outlined v-if="collapsed" /><menu-fold-outlined v-else />
          </span>
          <span :style="{ fontSize: '16px', fontWeight: 500, color: isDarkMode ? 'rgba(255,255,255,.85)' : 'var(--arl-text-color)' }">{{ currentPageTitle }}</span>
        </div>

        <div style="display: flex; align-items: center; color: var(--arl-text-color);">
          <a-dropdown>
            <span class="header-text-action" style="cursor: pointer; margin-right: 24px; display: flex; align-items: center;">
              <BgColorsOutlined style="font-size: 16px; margin-right: 4px;" />
              主题色
            </span>
            <template #overlay>
              <a-menu @click="handleThemeChange">
                <a-menu-item key="#00bcd4">
                  <span style="display: inline-block; width: 12px; height: 12px; background: #00bcd4; border-radius: 50%; margin-right: 8px;"></span>ARL 青
                </a-menu-item>
                <a-menu-item key="#1890ff">
                  <span style="display: inline-block; width: 12px; height: 12px; background: #1890ff; border-radius: 50%; margin-right: 8px;"></span>AntD 蓝
                </a-menu-item>
                <a-menu-item key="#52c41a">
                  <span style="display: inline-block; width: 12px; height: 12px; background: #52c41a; border-radius: 50%; margin-right: 8px;"></span>极客绿
                </a-menu-item>
                <a-menu-item key="#fa541c">
                  <span style="display: inline-block; width: 12px; height: 12px; background: #fa541c; border-radius: 50%; margin-right: 8px;"></span>火山橙
                </a-menu-item>
                <a-menu-item key="#eb2f96">
                  <span style="display: inline-block; width: 12px; height: 12px; background: #eb2f96; border-radius: 50%; margin-right: 8px;"></span>猛男粉
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>

          <a-upload :show-upload-list="false" :before-upload="handleUploadBackground" accept="image/*">
            <span class="header-text-action" style="cursor: pointer; margin-right: 24px; display: flex; align-items: center;">
              <PictureOutlined style="font-size: 16px; margin-right: 4px;" />
              自定义背景
            </span>
          </a-upload>

          <div style="margin-right: 24px; display: flex; align-items: center;" title="黑客暗色模式">
            <a-switch checked-children="🌙" un-checked-children="☀️" v-model:checked="isDarkMode" @change="toggleDarkMode" />
          </div>

          <span class="header-text-action" style="cursor: pointer; margin-right: 24px; display: flex; align-items: center;" @click="handleShowMcpModal">
            <RobotOutlined style="font-size: 16px; margin-right: 4px;" />
            AI 助手接入 (MCP)
          </span>
          
          <a-avatar style="background-color: #87d068; margin-right: 12px;" size="small"><template #icon><UserOutlined /></template></a-avatar>
          <span style="margin-right: 24px;">{{ currentUsername }}</span>
          
          <span class="header-text-action" style="cursor: pointer; margin-right: 24px;" @click="showChangePassModal = true">修改密码</span>
          
          <a-tooltip title="退出登录" placement="bottom">
            <span class="header-icon-action header-icon-danger" style="cursor: pointer;" @click="handleLogout">
              <LogoutOutlined style="font-size: 16px;" />
            </span>
          </a-tooltip>
        </div>
      </a-layout-header>

      <a-layout-content style="margin: 16px; display: flex; flex-direction: column;">
        <div :style="{ background: hasBgImage ? (isDarkMode ? 'rgba(15, 23, 42, 0.5)' : 'rgba(255, 255, 255, 0.4)') : (isDarkMode ? '#0f172a' : 'transparent'), flex: 1, borderRadius: '4px', overflow: 'hidden' }">
          <router-view></router-view>
        </div>
        <div :style="{ textAlign: 'center', padding: '16px 0', color: isDarkMode ? 'rgba(255,255,255,.45)' : 'rgba(0,0,0,.45)', fontSize: '12px' }">
          Powered by ARL-Next
        </div>
      </a-layout-content>
    </a-layout>
  </a-layout>
  <a-modal
      v-model:visible="showMcpModal"
      title="🚀 AI 助手 (MCP) 一键接入"
      @cancel="showMcpModal = false"
      :footer="null"
      width="640px"
      wrapClassName="arl-theme-modal"
      rootClassName="arl-theme-modal"
  >
    <div style="margin-bottom: 16px;">
      <p>想要使用 Cursor、Claude Desktop 或其他 AI 工具自动分析平台资产与漏洞？</p>
      <p>请选择传输模式，然后复制配置粘贴到 AI 客户端配置文件的 <code>"mcpServers"</code> 节点：</p>
    </div>
    <div style="margin-bottom: 16px; text-align: center;">
      <a-radio-group v-model:value="mcpMode" button-style="solid" @change="generateMcpConfig">
        <a-radio-button value="stdio">
          <span style="font-size: 15px; margin-right: 4px;">🐳</span> Docker (Stdio)
        </a-radio-button>
        <a-radio-button value="sse">
          <span style="font-size: 15px; margin-right: 4px;">🌐</span> HTTP (SSE)
        </a-radio-button>
      </a-radio-group>
    </div>
    <div v-if="mcpMode === 'sse'" style="margin-bottom: 16px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
      <span style="font-size: 13px;">SSE 服务器地址：</span>
      <a-input v-model:value="sseHost" style="width: 200px;" size="small" placeholder="http://localhost" @change="generateMcpConfig" />
      <span style="font-size: 13px;">端口：</span>
      <a-input-number v-model:value="ssePort" :min="1024" :max="65535" size="small" style="width: 80px;" @change="generateMcpConfig" />
    </div>
    <div style="position: relative;">
      <pre :style="{ background: hasBgImage ? 'rgba(0,0,0,0.2)' : 'var(--arl-bg-light)', padding: '16px', borderRadius: '4px', overflowX: 'auto', fontSize: '13px', border: hasBgImage ? '1px solid rgba(255,255,255,0.1)' : 'none' }"><code :style="{ color: hasBgImage ? 'var(--arl-text-color)' : 'inherit' }">{{ mcpConfigJson }}</code></pre>
      <div style="position: absolute; top: 12px; right: 12px; display: flex; gap: 8px;">
        <a-button type="default" size="small" :loading="isRefreshingToken" @click="refreshMcpToken">刷新 Token</a-button>
        <a-button type="primary" size="small" @click="copyMcpConfig">复制配置</a-button>
      </div>
    </div>
    <div v-if="mcpMode === 'stdio'" style="margin-top: 16px; font-size: 12px; color: var(--arl-text-color); opacity: 0.65;">
      <span>⚡ Stdio 模式：每次调用拉起短生命周期容器，调用结束即销毁。需先构建镜像：<code>docker build -t arl-next-mcp:latest ./mcp-server</code>。配置包含 API Token，请妥善保管。</span>
    </div>
    <div v-else style="margin-top: 16px; font-size: 12px; color: var(--arl-text-color); opacity: 0.65;">
      <span>🌐 SSE 模式：MCP 服务器以持久化 HTTP 服务运行，适合 IDE 插件和远程客户端。部署命令：<code style="word-break: break-all;">docker run -d --name arl-next-mcp -p {{ ssePort }}:{{ ssePort }} -e ARL_HOST={{ apiHost }} -e ARL_TOKEN=... -e SSE=true -e PORT={{ ssePort }} arl-next-mcp:latest</code>（需先构建镜像）</span>
    </div>
  </a-modal>

  <a-modal
      v-model:visible="showChangePassModal"
      title="修改密码"
      @ok="handleChangePass"
      :confirmLoading="isSubmitting"
      @cancel="handleCancelChangePass"
      okText="确认修改"
      cancelText="取消"
  >
    <a-form :model="passForm" :rules="passRules" ref="passFormRef" layout="vertical">
      <a-form-item label="旧密码" name="old_password">
        <a-input-password v-model:value="passForm.old_password" placeholder="请输入旧密码" />
      </a-form-item>
      <a-form-item label="新密码" name="new_password">
        <a-input-password v-model:value="passForm.new_password" placeholder="请输入新密码" />
      </a-form-item>
      <a-form-item label="确认新密码" name="check_password">
        <a-input-password v-model:value="passForm.check_password" placeholder="请再次输入新密码" />
      </a-form-item>
    </a-form>
  </a-modal>

  <!-- 沉浸式背景屏幕保护叠加层 -->
  <div class="screensaver-overlay" :class="{ 'is-active': isUIHidden }">
    <div class="screensaver-content">
      <div class="screensaver-time">{{ currentTime }}</div>
      <div class="screensaver-brand">
        <DeploymentUnitOutlined class="screensaver-icon" />
        <span>ARL-Next OS</span>
      </div>
      <div class="screensaver-tip">Monitoring assets... Click anywhere to resume.</div>
    </div>
  </div>
</template>

<script setup>
import { ref,reactive, onMounted, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
// 引入 request (根据你的实际路径调整)
import request from '@/utils/request';
// 引入主题提取工具和 IndexedDB
import { extractDominantColor, processImageToBase64, dbHelper } from '@/utils/theme';
// 引入 Ant Design 的消息提示
import { message } from 'ant-design-vue';

// 补全所有需要的图标
import { DashboardOutlined, MenuUnfoldOutlined, MenuFoldOutlined, UserOutlined, LogoutOutlined, GlobalOutlined, SearchOutlined, DesktopOutlined, AppstoreOutlined, SettingOutlined, TagsOutlined, BugOutlined, ClockCircleOutlined, GithubOutlined, EyeOutlined, DeploymentUnitOutlined, RobotOutlined, BgColorsOutlined, PictureOutlined, UploadOutlined, DeleteOutlined } from '@ant-design/icons-vue';

const route = useRoute();
const router = useRouter();
const collapsed = ref(false);
const selectedKeys = ref([route.path]);
const isDarkMode = ref(false);
const currentUsername = ref('admin');
const hasBgImage = ref(false);
const isUIHidden = ref(false);

const currentTime = ref('');
let timeInterval = null;

const updateTime = () => {
  const now = new Date();
  const hours = now.getHours().toString().padStart(2, '0');
  const mins = now.getMinutes().toString().padStart(2, '0');
  currentTime.value = `${hours}:${mins}`;
};

const toggleUI = (e) => {
  if (!hasBgImage.value) return;
  e.stopPropagation();
  isUIHidden.value = !isUIHidden.value;
  if (isUIHidden.value) {
    document.body.classList.add('ui-hidden');
  } else {
    document.body.classList.remove('ui-hidden');
  }
};

const restoreUI = () => {
  if (isUIHidden.value) {
    isUIHidden.value = false;
    document.body.classList.remove('ui-hidden');
  }
};

const toggleDarkMode = (checked) => {
  isDarkMode.value = checked;
  localStorage.setItem('darkMode', checked ? 'true' : 'false');
  window.dispatchEvent(new CustomEvent('dark-mode-changed', { detail: checked }));
};

const handleThemeChange = async (e) => {
  const color = e.key;
  localStorage.setItem('themeColor', color);
  await dbHelper.remove('bgImage'); // 恢复纯色主题时移除背景图片
  hasBgImage.value = false;
  window.dispatchEvent(new CustomEvent('theme-changed', { detail: color }));
  window.dispatchEvent(new CustomEvent('bg-image-changed', { detail: '' }));
  message.success('主题色已切换');
};

const handleUploadBackground = async (file) => {
  // 由于读取和提取可能较慢，可以给个 Loading 提示
  const hide = message.loading('正在提取主题色并设置高清背景...', 0);
  try {
    const base64 = await processImageToBase64(file);
    const color = await extractDominantColor(base64);
    
    localStorage.setItem('themeColor', color);
    await dbHelper.set('bgImage', base64);
    
    window.dispatchEvent(new CustomEvent('theme-changed', { detail: color }));
    window.dispatchEvent(new CustomEvent('bg-image-changed', { detail: base64 }));
    
    hide();
    message.success('自定义高清主题背景设置成功！');
  } catch (e) {
    hide();
    message.error('提取颜色或设置失败：' + e.message);
  }
  return false; // 拦截默认上传行为
};

const handleBgImageEvent = (e) => {
  hasBgImage.value = !!e.detail;
};

onMounted(() => {
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
  if (userInfo.username) currentUsername.value = userInfo.username;
  
  if (route.path.includes('/GitHubTasks/')) {
    selectedKeys.value = ['/GitHubTasks/GitHubTasksList'];
  }
  
  const savedDarkMode = localStorage.getItem('darkMode');
  if (savedDarkMode === 'true') {
    isDarkMode.value = true;
  }
  
  dbHelper.get('bgImage').then((bgImage) => {
    if (bgImage) {
      hasBgImage.value = true;
    }
  });
  
  window.addEventListener('bg-image-changed', handleBgImageEvent);
  document.addEventListener('click', restoreUI);

  updateTime();
  timeInterval = setInterval(updateTime, 1000);
});

import { onUnmounted } from 'vue';
onUnmounted(() => {
  window.removeEventListener('bg-image-changed', handleBgImageEvent);
  document.removeEventListener('click', restoreUI);
  if (timeInterval) clearInterval(timeInterval);
});

const handleMenuClick = (e) => router.push(e.key);

const handleLogout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('userInfo');
  router.push('/login');
};

// 监听路由变化，保持左侧菜单高亮的一致性
watch(() => route.path, (newPath) => {
  // 如果当前在详情页，依然让“任务管理”菜单亮起
  if (newPath.startsWith('/taskList')) {
    selectedKeys.value = ['/taskList'];
  } else if (newPath.startsWith('/assetRecon')) {
    selectedKeys.value = ['/assetRecon'];
  } else {
    selectedKeys.value = [newPath];
  }
}, { immediate: true });

// 动态计算页面标题
const currentPageTitle = computed(() => {
  if (route.path.includes('taskDetail')) return '任务详情'; // 详情页标题
  if (route.path.includes('assetRecon/assetDetail')) return '企业信息资产详情'; // ICP详情页
  const titleMap = {
    '/dashboard': '仪表盘',
    '/assetRecon': '企业资产查询',
    '/group': '资产分组',
    '/taskList': '任务管理',
    '/asset-search': '资产搜索',
    '/assetsMonitor': '资产监控',
    '/planningTasks': '计划任务',
    '/GitHubTasks/GitHubTasksList': 'GitHub监控',
    '/policy': '策略配置',
    '/pocList': 'POC管理',
    '/fingerprint': '指纹管理',
    '/systemSettings': '系统设置',
  };
  return titleMap[route.path] || 'ARL-Next';
});
/* ---------- 新增：修改密码逻辑 ---------- */
const showChangePassModal = ref(false);
const isSubmitting = ref(false);
const passFormRef = ref();

// 表单数据绑定
const passForm = reactive({
  old_password: '',
  new_password: '',
  check_password: ''
});

// 自定义校验：确认密码必须和新密码一致
const validateCheckPassword = async (_rule, value) => {
  if (value === '') {
    return Promise.reject('请再次输入确认密码');
  } else if (value !== passForm.new_password) {
    return Promise.reject('两次输入的新密码不一致!');
  } else {
    return Promise.resolve();
  }
};

// 表单校验规则
const passRules = {
  old_password: [{ required: true, message: '旧密码不能为空', trigger: 'blur' }],
  new_password: [{ required: true, message: '新密码不能为空', trigger: 'blur' }],
  check_password: [{ required: true, validator: validateCheckPassword, trigger: 'blur' }]
};

// 提交修改密码
const handleChangePass = async () => {
  try {
    // 1. 触发前端表单验证
    await passFormRef.value.validate();
    isSubmitting.value = true;

    // 2. 发送请求给后端（注意检查这里的 URL 是否需要加 /api 前缀，取决于你的 request.js baseURL 配置）
    const res = await request.post('/user/change_pass', passForm);

    // 3. 处理后端返回结果
    if (res.code === 200) {
      message.success('密码修改成功，请重新登录');
      showChangePassModal.value = false;
      passFormRef.value.resetFields();
      handleLogout(); // 密码修改成功后调用已有的退出逻辑
    } else {
      // 捕获后端的 301, 302, 303 等错误
      message.error(res.message || '修改失败');
    }
  } catch (error) {
    console.error('表单校验失败或网络错误:', error);
  } finally {
    isSubmitting.value = false;
  }
};

// 取消弹窗时重置表单
const handleCancelChangePass = () => {
  passFormRef.value?.resetFields();
};

/* ---------- MCP 接入逻辑（支持 Stdio / SSE 双模式） ---------- */
const showMcpModal = ref(false);
const mcpConfigJson = ref('');
const mcpMode = ref('stdio');
const ssePort = ref(3100);
const sseHost = ref('');

const apiHost = computed(() => {
  const loc = window.location;
  const apiPort = loc.port === '5173' ? '5001' : loc.port;
  return loc.protocol + '//' + loc.hostname + ':' + apiPort;
});

function generateMcpConfig() {
  const token = localStorage.getItem('token') || 'YOUR_API_TOKEN';
  let config;
  if (mcpMode.value === 'sse') {
    const host = sseHost.value || apiHost.value;
    config = {
      "ARL-Next": {
        "url": host + ':' + ssePort.value + '/sse'
      }
    };
  } else {
    config = {
      "ARL-Next": {
        "command": "docker",
        "args": [
          "run",
          "-i",
          "--rm",
          "-e",
          "ARL_HOST",
          "-e",
          "ARL_TOKEN",
          "arl-next-mcp:latest"
        ],
        "env": {
          "ARL_HOST": apiHost.value,
          "ARL_TOKEN": token
        }
      }
    };
  }
  const jsonStr = JSON.stringify(config, null, 2);
  mcpConfigJson.value = jsonStr.substring(2, jsonStr.length - 2).trim();
}

const handleShowMcpModal = () => {
  sseHost.value = apiHost.value;
  generateMcpConfig();
  showMcpModal.value = true;
};

const copyMcpConfig = () => {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(mcpConfigJson.value).then(() => {
      message.success('MCP 配置已复制到剪贴板！');
    }).catch(() => {
      message.error('复制失败，请手动选择复制');
    });
  } else {
    message.error('当前环境不支持一键复制，请手动选择复制');
  }
};

const isRefreshingToken = ref(false);
const refreshMcpToken = async () => {
  try {
    isRefreshingToken.value = true;
    const res = await request.post('/user/refresh_token');
    if (res.code === 200 && res.data && res.data.token) {
      localStorage.setItem('token', res.data.token);
      message.success('Token 已作废并刷新成功，配置已自动更新！');
      generateMcpConfig(); // 重新生成配置展示
    } else {
      message.error(res.message || '刷新 Token 失败');
    }
  } catch (error) {
    message.error('刷新 Token 失败，请检查网络');
  } finally {
    isRefreshingToken.value = false;
  }
};
</script>

<style scoped>
.header-icon-action {
  color: var(--arl-text-color);
  transition: color 0.3s;
}
.header-icon-action:hover {
  color: var(--arl-theme-color);
}
.header-text-action {
  color: var(--arl-text-color);
  transition: color 0.3s;
}
.header-text-action:hover {
  color: var(--arl-theme-color);
}
.header-icon-danger {
  color: var(--arl-text-color);
  transition: color 0.3s;
}
.header-icon-danger:hover {
  color: #ff4d4f;
}

/* 屏幕保护叠加层 */
.screensaver-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  pointer-events: none;
  z-index: 99;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.8s ease-in-out;
}
.screensaver-overlay.is-active {
  opacity: 1;
}
.screensaver-content {
  text-align: center;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 2px 10px rgba(0,0,0,0.5);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
.screensaver-time {
  font-size: 72px;
  font-weight: 200;
  letter-spacing: 4px;
  margin-bottom: 8px;
}
.screensaver-brand {
  font-size: 24px;
  font-weight: 500;
  letter-spacing: 8px;
  text-transform: uppercase;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}
.screensaver-icon {
  font-size: 28px;
  color: var(--arl-theme-color);
  animation: pulse-ring 2s infinite;
}
.screensaver-tip {
  font-size: 14px;
  opacity: 0.6;
  letter-spacing: 2px;
}
@keyframes pulse-ring {
  0% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.1); opacity: 1; text-shadow: 0 0 15px var(--arl-theme-color); }
  100% { transform: scale(1); opacity: 0.8; }
}
</style>
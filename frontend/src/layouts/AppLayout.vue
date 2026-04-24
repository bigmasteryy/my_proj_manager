<template>
  <el-container style="min-height: 100vh;">
    <el-aside width="220px" class="app-aside">
      <div class="brand-box">
        <p class="eyebrow">项目管理</p>
        <h1>项目管理平台</h1>
      </div>

      <el-menu
        :default-active="route.path"
        :default-openeds="defaultOpeneds"
        class="app-menu"
        router
      >
        <el-menu-item v-if="isAdmin" index="/dashboard">
          <el-icon><House /></el-icon>
          <span>首页驾驶舱</span>
        </el-menu-item>

        <el-sub-menu v-if="isAdmin" index="project-group">
          <template #title>
            <span class="menu-title">
              <el-icon><DataBoard /></el-icon>
              <span>项目进度</span>
            </span>
          </template>
          <el-menu-item index="/progress/overview">
            <el-icon><Tickets /></el-icon>
            <span>项目总览</span>
          </el-menu-item>
          <el-menu-item index="/progress/matrix">
            <el-icon><List /></el-icon>
            <span>推进矩阵</span>
          </el-menu-item>
          <el-menu-item index="/progress/brokers">
            <el-icon><Tickets /></el-icon>
            <span>券商视图</span>
          </el-menu-item>
          <el-menu-item index="/progress/logs">
            <el-icon><Reading /></el-icon>
            <span>推进记录</span>
          </el-menu-item>
          <el-menu-item index="/progress/risks">
            <el-icon><WarningFilled /></el-icon>
            <span>风险与阻塞</span>
          </el-menu-item>
          <el-menu-item index="/progress/reports">
            <el-icon><Document /></el-icon>
            <span>项目周报</span>
          </el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="personal-group">
          <template #title>
            <span class="menu-title">
              <el-icon><UserFilled /></el-icon>
              <span>个人任务</span>
            </span>
          </template>
          <el-menu-item index="/personal/daily">
            <el-icon><Calendar /></el-icon>
            <span>每日任务</span>
          </el-menu-item>
          <el-menu-item index="/personal/long-term">
            <el-icon><List /></el-icon>
            <span>长期任务</span>
          </el-menu-item>
          <el-menu-item index="/personal/risks">
            <el-icon><Warning /></el-icon>
            <span>个人风险</span>
          </el-menu-item>
          <el-menu-item index="/personal/reports">
            <el-icon><DocumentCopy /></el-icon>
            <span>个人周报</span>
          </el-menu-item>
          <el-menu-item index="/history/personal">
            <el-icon><Clock /></el-icon>
            <span>个人历史</span>
          </el-menu-item>
        </el-sub-menu>

        <el-menu-item v-if="isAdmin" index="/templates">
          <el-icon><CollectionTag /></el-icon>
          <span>模板中心</span>
        </el-menu-item>

        <el-menu-item v-if="currentUser?.role === 'admin'" index="/users">
          <el-icon><UserFilled /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
      </el-menu>

      <div class="focus-box">
        <p class="eyebrow">今日关注</p>
        <p class="compact-note">{{ isAdmin ? "优先处理逾期、高风险和关键节点事项。" : "优先处理自己的到期任务和个人风险事项。" }}</p>
      </div>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <div>
          <p class="eyebrow">管理视图</p>
          <h2>{{ isAdmin ? "项目总控台" : "个人任务中心" }}</h2>
        </div>
        <div class="header-actions">
          <span class="compact-note" v-if="currentUser">{{ currentUser.displayName }} / {{ roleLabel }}</span>
          <el-button v-if="currentUser?.role === 'admin'" @click="handleResetDemoData">重置演示数据</el-button>
          <el-button type="primary" @click="router.push(isAdmin ? '/progress/overview' : '/personal/daily')">
            {{ isAdmin ? "查看项目总览" : "查看每日任务" }}
          </el-button>
          <el-button @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="app-main">
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { RouterView, useRoute, useRouter } from "vue-router";
import {
  Calendar,
  Clock,
  CollectionTag,
  DataBoard,
  Document,
  DocumentCopy,
  House,
  List,
  Reading,
  Tickets,
  UserFilled,
  Warning,
  WarningFilled
} from "@element-plus/icons-vue";

import { getCurrentUserProfile, logout } from "../api/auth";
import { resetDemoData } from "../api/system";
import type { AuthUser } from "../types/models";
import { clearSession, getStoredUser } from "../utils/auth";

const route = useRoute();
const router = useRouter();
const currentUser = ref<AuthUser | null>(getStoredUser());
const isAdmin = computed(() => currentUser.value?.role === "admin");
const defaultOpeneds = computed(() => (isAdmin.value ? ["project-group", "personal-group"] : ["personal-group"]));
const roleLabel = computed(() => {
  if (currentUser.value?.role === "admin") {
    return "管理员";
  }
  if (currentUser.value?.role === "user") {
    return "普通用户";
  }
  return currentUser.value?.role || "";
});

async function handleResetDemoData() {
  try {
    await ElMessageBox.confirm(
      "确定要重置演示数据吗？当前录入内容会恢复为默认示例。",
      "重置演示数据",
      {
        type: "warning",
        confirmButtonText: "确认重置",
        cancelButtonText: "取消"
      }
    );
  } catch {
    return;
  }

  await resetDemoData();
  ElMessage.success("演示数据已重置");
  await router.push("/progress/overview");
  window.location.reload();
}

async function handleLogout() {
  try {
    await logout();
  } catch {
    // noop
  }
  clearSession();
  router.push("/login");
}

onMounted(async () => {
  try {
    currentUser.value = await getCurrentUserProfile();
  } catch {
    clearSession();
    router.push("/login");
  }
});
</script>

<style scoped>
.app-aside {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px 14px;
  border-right: 1px solid var(--border);
  background: rgba(255, 251, 245, 0.84);
  backdrop-filter: blur(16px);
}

.brand-box,
.focus-box {
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: var(--shadow);
}

.brand-box h1,
.app-header h2 {
  margin: 0;
  font-size: 26px;
  line-height: 1.15;
}

.brand-box p,
.compact-note {
  color: var(--text-subtle);
  margin: 0;
  line-height: 1.6;
  font-size: 14px;
}

.app-menu {
  border-right: 0;
  border-radius: 14px;
  overflow: hidden;
}

.menu-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
}

.app-menu :deep(.el-menu-item),
.app-menu :deep(.el-sub-menu__title) {
  border-radius: 12px;
}

.app-menu :deep(.el-menu-item.is-active) {
  background: rgba(15, 109, 121, 0.12);
  color: var(--brand);
  font-weight: 600;
}

.app-menu :deep(.el-menu-item:hover),
.app-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(15, 109, 121, 0.08);
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  height: auto;
  padding: 22px 28px 10px;
}

.app-main {
  padding: 12px 28px 28px;
}

.header-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

@media (max-width: 980px) {
  .app-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

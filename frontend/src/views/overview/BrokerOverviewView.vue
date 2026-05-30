<template>
  <div class="page-shell">
    <section class="compact-toolbar">
      <div>
        <p class="eyebrow">券商总览</p>
        <h2>先看券商整体状态，再进入项目视图或资产明细。</h2>
      </div>
      <div class="hero-actions compact">
        <el-button @click="router.push('/brokers')">券商列表</el-button>
        <el-button type="primary" @click="router.push('/progress/brokers')">券商项目视图</el-button>
      </div>
    </section>

    <section class="compact-grid broker-stat-grid">
      <article class="compact-card">
        <small>覆盖券商</small>
        <strong>{{ overview.summary.totalBrokers }}</strong>
      </article>
      <article class="compact-card">
        <small>已上线</small>
        <strong>{{ overview.summary.onlineBrokers }}</strong>
      </article>
      <article class="compact-card">
        <small>对接中 / 灰度中</small>
        <strong>{{ overview.summary.connectingBrokers }} / {{ overview.summary.grayBrokers }}</strong>
      </article>
      <article class="compact-card">
        <small>服务器 / 委托主站</small>
        <strong>{{ overview.summary.totalServers }} / {{ overview.summary.totalEntrustSites }}</strong>
      </article>
      <article class="compact-card">
        <small>风险券商</small>
        <strong>{{ overview.summary.riskBrokers }}</strong>
      </article>
    </section>

    <section class="broker-overview-layout">
      <div class="broker-overview-main">
        <section class="section-card">
          <div class="section-title">
            <div>
              <h3>重点券商</h3>
              <p>优先展示有风险、未完成项目较多或推进活跃的券商。</p>
            </div>
            <el-button size="small" @click="openFeaturedDialog">编辑重点券商</el-button>
          </div>
          <div v-if="overview.focusBrokers.length" class="focus-broker-grid">
            <article
              v-for="item in overview.focusBrokers"
              :key="item.id"
              class="focus-broker-card"
              @click="openBrokerProjects(item.id)"
            >
              <div class="broker-card-head">
                <div>
                  <strong>{{ item.name }}</strong>
                  <small>{{ item.shortName }} · {{ item.systemVersion }}</small>
                </div>
                <StatusTag :label="item.businessStatus" />
              </div>
              <el-progress :percentage="item.avgProgress" :stroke-width="8" />
              <div class="broker-card-metrics">
                <span>项目 {{ item.progressProjectCount }}</span>
                <span>未完成 {{ item.unfinishedProjectCount }}</span>
                <span>风险 {{ item.riskCount }}</span>
              </div>
            </article>
          </div>
          <EmptyBlock
            v-else
            title="当前还没有重点券商"
            description="点击“编辑重点券商”，选择最多 6 个券商展示在这里。"
          />
        </section>

        <section class="section-card">
          <div class="section-title">
            <div>
              <h3>完整券商总表</h3>
              <p>统一查看券商状态、基础资产、项目推进和风险情况。</p>
            </div>
          </div>
          <el-table
            v-if="overview.brokerRows.length"
            :data="overview.brokerRows"
            stripe
            v-loading="loading"
          >
            <el-table-column prop="name" label="券商" min-width="150" sortable />
            <el-table-column prop="businessStatus" label="状态" min-width="100" sortable>
              <template #default="{ row }">
                <StatusTag :label="row.businessStatus" />
              </template>
            </el-table-column>
            <el-table-column prop="systemVersion" label="系统版本" min-width="110" sortable />
            <el-table-column prop="serverCount" label="服务器" min-width="90" sortable />
            <el-table-column prop="entrustSiteCount" label="委托主站" min-width="100" sortable />
            <el-table-column prop="progressProjectCount" label="推进项目" min-width="100" sortable />
            <el-table-column prop="unfinishedProjectCount" label="未完成" min-width="90" sortable />
            <el-table-column prop="avgProgress" label="平均进度" min-width="110" sortable>
              <template #default="{ row }">{{ row.avgProgress }}%</template>
            </el-table-column>
            <el-table-column prop="riskCount" label="风险" min-width="80" sortable />
            <el-table-column prop="latestUpdateAt" label="最近更新" min-width="110" sortable>
              <template #default="{ row }">{{ row.latestUpdateAt || "-" }}</template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openBrokerProjects(row.id)">项目</el-button>
                <el-button link type="primary" @click="router.push(`/brokers?brokerId=${row.id}`)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
          <EmptyBlock
            v-else
            title="当前还没有券商数据"
            description="新增券商后，这里会汇总所有券商。"
          />
        </section>
      </div>

      <aside class="broker-overview-side">
        <section class="section-card">
          <div class="section-title">
            <div>
              <h3>待跟进券商</h3>
              <p>有未完成推进项目或风险的券商会集中显示在这里。</p>
            </div>
          </div>
          <div v-if="overview.followUpBrokers.length" class="quick-list">
            <button
              v-for="item in overview.followUpBrokers"
              :key="item.id"
              class="broker-list-item"
              type="button"
              @click="openBrokerProjects(item.id)"
            >
              <div class="broker-list-head">
                <strong>{{ item.name }}</strong>
                <StatusTag :label="item.businessStatus" />
              </div>
              <div class="broker-list-meta">
                <span>未完成 {{ item.unfinishedProjectCount }}/{{ item.progressProjectCount }}</span>
                <span>平均 {{ item.avgProgress }}%</span>
                <span>风险 {{ item.riskCount }}</span>
              </div>
              <small>最近更新：{{ item.latestUpdateAt || "-" }}</small>
            </button>
          </div>
          <EmptyBlock
            v-else
            title="当前没有待跟进券商"
            description="所有券商推进平稳时，这里会保持为空。"
          />
        </section>

        <section class="section-card">
          <div class="section-title">
            <div>
              <h3>券商风险提醒</h3>
              <p>来自推进项目中的高风险或阻塞事项。</p>
            </div>
          </div>
          <div v-if="overview.riskHighlights.length" class="quick-list">
            <article
              v-for="item in overview.riskHighlights"
              :key="item.id"
              class="broker-risk-item"
            >
              <div class="broker-list-head">
                <strong>{{ item.title }}</strong>
                <StatusTag :label="item.level" />
              </div>
              <div class="broker-list-meta">
                <span>{{ item.brokerName }}</span>
                <span>{{ item.projectName }}</span>
              </div>
              <small>{{ item.status }} · {{ item.updatedAt || "-" }}</small>
            </article>
          </div>
          <EmptyBlock
            v-else
            title="当前没有券商风险"
            description="新增风险或阻塞后，这里会集中展示。"
          />
        </section>
      </aside>
    </section>

    <el-dialog v-model="featuredDialogVisible" title="编辑重点券商" width="620px">
      <p class="featured-dialog-tip">选择最多 6 个券商展示在“重点券商”区域，保存后立即生效。</p>
      <el-checkbox-group v-model="featuredBrokerIds" :max="6" class="featured-broker-options">
        <el-checkbox
          v-for="item in overview.brokerRows"
          :key="item.id"
          :label="item.id"
        >
          <span class="featured-option">
            <strong>{{ item.name }}</strong>
            <small>
              {{ item.businessStatus }} · 推进项目 {{ item.progressProjectCount }} · 未完成 {{ item.unfinishedProjectCount }} · 风险 {{ item.riskCount }}
            </small>
          </span>
        </el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="featuredDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="featuredSaving" @click="saveFeaturedBrokers">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import EmptyBlock from "../../components/EmptyBlock.vue";
import StatusTag from "../../components/StatusTag.vue";
import { getBrokerOverview, updateBrokerFeatured } from "../../api/brokers";
import type { BrokerOverview } from "../../types/models";

const router = useRouter();
const loading = ref(false);
const featuredDialogVisible = ref(false);
const featuredSaving = ref(false);
const featuredBrokerIds = ref<number[]>([]);
const overview = ref<BrokerOverview>({
  summary: {
    totalBrokers: 0,
    onlineBrokers: 0,
    connectingBrokers: 0,
    grayBrokers: 0,
    totalServers: 0,
    totalEntrustSites: 0,
    riskBrokers: 0
  },
  focusBrokers: [],
  brokerRows: [],
  followUpBrokers: [],
  riskHighlights: []
});

function openBrokerProjects(brokerId: number) {
  router.push(`/progress/brokers?brokerId=${brokerId}`);
}

function openFeaturedDialog() {
  featuredBrokerIds.value = overview.value.focusBrokers.map((item) => item.id);
  featuredDialogVisible.value = true;
}

async function saveFeaturedBrokers() {
  featuredSaving.value = true;
  try {
    await updateBrokerFeatured({ broker_ids: featuredBrokerIds.value });
    await loadOverview();
    featuredDialogVisible.value = false;
    ElMessage.success("重点券商已更新");
  } finally {
    featuredSaving.value = false;
  }
}

async function loadOverview() {
  loading.value = true;
  try {
    overview.value = await getBrokerOverview();
  } finally {
    loading.value = false;
  }
}

onMounted(loadOverview);
</script>

<style scoped>
.broker-stat-grid {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.broker-overview-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.85fr) minmax(320px, 0.85fr);
  gap: 16px;
  align-items: start;
}

.broker-overview-main,
.broker-overview-side {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.focus-broker-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.focus-broker-card,
.broker-list-item,
.broker-risk-item {
  width: 100%;
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface-muted);
  text-align: left;
}

.featured-dialog-tip {
  margin: 0 0 12px;
  color: var(--text-subtle);
  line-height: 1.6;
}

.featured-broker-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 460px;
  overflow: auto;
}

.featured-broker-options :deep(.el-checkbox) {
  height: auto;
  align-items: flex-start;
  margin-right: 0;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface-muted);
}

.featured-option {
  display: flex;
  flex-direction: column;
  gap: 4px;
  white-space: normal;
}

.featured-option strong {
  color: var(--text-main);
}

.featured-option small {
  color: var(--text-subtle);
}

.focus-broker-card,
.broker-list-item {
  cursor: pointer;
}

.focus-broker-card:hover,
.broker-list-item:hover {
  border-color: rgba(15, 109, 121, 0.26);
  background: rgba(255, 255, 255, 0.94);
}

.broker-card-head,
.broker-list-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 10px;
}

.broker-card-head strong,
.broker-list-head strong {
  display: block;
  margin-bottom: 4px;
  color: var(--text-main);
}

.broker-card-head small,
.broker-list-item small,
.broker-risk-item small {
  color: var(--text-subtle);
}

.broker-card-metrics,
.broker-list-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 10px;
  color: var(--text-subtle);
  font-size: 13px;
}

@media (max-width: 1280px) {
  .focus-broker-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1100px) {
  .broker-overview-layout {
    grid-template-columns: 1fr;
  }

  .broker-stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .focus-broker-grid,
  .broker-stat-grid {
    grid-template-columns: 1fr;
  }
}
</style>

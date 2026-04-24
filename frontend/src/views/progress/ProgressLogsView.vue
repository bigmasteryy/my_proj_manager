<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">推进记录</p>
        <h2>把推进过程和里程碑集中到一页回看，方便复盘和周报引用。</h2>
        <p>支持按项目、券商和里程碑筛选最近的推进过程。</p>
      </div>
    </section>

    <section class="section-card">
      <div class="filter-grid">
        <el-select v-model="filters.projectTemplateId" clearable placeholder="全部项目">
          <el-option v-for="item in projects" :key="item.projectTemplateId" :label="item.projectName" :value="item.projectTemplateId" />
        </el-select>
        <el-select v-model="filters.brokerId" clearable placeholder="全部券商">
          <el-option v-for="item in brokers" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <el-input v-model="filters.keyword" clearable placeholder="搜索推进内容" />
        <el-select v-model="filters.onlyMilestone" placeholder="全部记录">
          <el-option label="全部记录" :value="false" />
          <el-option label="只看里程碑" :value="true" />
        </el-select>
      </div>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>推进记录列表</h3>
          <p>当前共 {{ logs.length }} 条记录。</p>
        </div>
        <el-button type="primary" @click="loadLogs">刷新</el-button>
      </div>
      <el-table v-if="logs.length" :data="logs" stripe max-height="560">
        <el-table-column prop="logDate" label="日期" min-width="110" sortable />
        <el-table-column prop="projectName" label="项目" min-width="140" sortable />
        <el-table-column prop="brokerName" label="券商" min-width="110" sortable />
        <el-table-column prop="itemLabel" label="进度项" min-width="110" sortable />
        <el-table-column label="推进内容" min-width="240">
          <template #default="{ row }">
            <div class="table-multiline">{{ row.content }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="progressDelta" label="进度变化" min-width="90" sortable>
          <template #default="{ row }">+{{ row.progressDelta }}%</template>
        </el-table-column>
        <el-table-column prop="progressAfter" label="当前进度" min-width="90" sortable>
          <template #default="{ row }">{{ row.progressAfter }}%</template>
        </el-table-column>
        <el-table-column prop="isMilestone" label="里程碑" min-width="90" sortable>
          <template #default="{ row }">
            <StatusTag :label="row.isMilestone ? '里程碑' : '普通记录'" />
          </template>
        </el-table-column>
      </el-table>
      <EmptyBlock
        v-else
        title="当前没有匹配的推进记录"
        description="新增推进记录或调整筛选条件后，这里会展示完整时间线。"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";

import EmptyBlock from "../../components/EmptyBlock.vue";
import StatusTag from "../../components/StatusTag.vue";
import { getProgressBrokers, getProgressLogs, getProgressProjects } from "../../api/progress";
import type { ProgressBrokerSimple, ProgressLogItem, ProgressProjectSummary } from "../../types/models";

const projects = ref<ProgressProjectSummary[]>([]);
const brokers = ref<ProgressBrokerSimple[]>([]);
const logs = ref<ProgressLogItem[]>([]);

const filters = reactive({
  projectTemplateId: undefined as number | undefined,
  brokerId: undefined as number | undefined,
  keyword: "",
  onlyMilestone: false
});

async function loadLogs() {
  logs.value = await getProgressLogs({
    project_template_id: filters.projectTemplateId,
    broker_id: filters.brokerId,
    keyword: filters.keyword,
    only_milestone: filters.onlyMilestone
  });
}

onMounted(async () => {
  [projects.value, brokers.value] = await Promise.all([getProgressProjects(), getProgressBrokers()]);
  await loadLogs();
});

watch(
  () => ({ ...filters }),
  async () => {
    await loadLogs();
  },
  { deep: true }
);
</script>

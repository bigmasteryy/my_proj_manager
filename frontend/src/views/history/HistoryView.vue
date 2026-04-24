<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">项目历史</p>
        <h2>查询项目历史记录，回看谁在什么时候推进了什么。</h2>
        <p>这里仅保留项目相关历史，不和个人任务历史混在一起。</p>
      </div>
      <div style="display: flex; gap: 12px; flex-wrap: wrap;">
        <el-button @click="resetFilters">重置筛选</el-button>
        <el-button @click="copyHistoryText">复制结果</el-button>
        <el-button @click="downloadHistoryCsv">导出 CSV</el-button>
        <el-button type="primary" @click="loadHistory">查询历史</el-button>
      </div>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>筛选条件</h3>
          <p>支持按券商、项目和关键词定位历史记录。</p>
        </div>
      </div>
      <div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px;">
        <el-form-item label="券商" style="margin-bottom: 0;">
          <el-select v-model="filters.broker_id" clearable placeholder="全部券商" @change="handleBrokerChange">
            <el-option v-for="broker in brokers" :key="broker.id" :label="broker.name" :value="broker.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目" style="margin-bottom: 0;">
          <el-select v-model="filters.project_id" clearable placeholder="全部项目">
            <el-option
              v-for="project in filteredProjects"
              :key="project.id"
              :label="project.projectName"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词" style="margin-bottom: 0;">
          <el-input v-model="filters.keyword" placeholder="可搜内容、下一步、项目名" @keyup.enter="loadHistory" />
        </el-form-item>
        <el-form-item label="时间范围" style="margin-bottom: 0;">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%;"
          />
        </el-form-item>
      </div>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>项目历史</h3>
          <p>当前共查询到 {{ historyLogs.length }} 条记录。</p>
        </div>
      </div>
      <el-table v-if="historyLogs.length" :data="historyLogs" stripe>
        <el-table-column prop="logDate" label="记录时间" min-width="150" />
        <el-table-column prop="brokerName" label="券商" min-width="120" />
        <el-table-column prop="projectName" label="项目" min-width="220" />
        <el-table-column prop="projectType" label="类型" min-width="120" />
        <el-table-column prop="content" label="跟进内容" min-width="260" show-overflow-tooltip />
        <el-table-column prop="nextAction" label="下一步动作" min-width="260" show-overflow-tooltip />
        <el-table-column label="操作" min-width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/projects/${row.projectId}`)">查看项目</el-button>
          </template>
        </el-table-column>
      </el-table>
      <EmptyBlock
        v-else
        title="暂时没有项目历史"
        description="可以先清空筛选条件重新查询，或到项目详情里新增跟进记录。"
      >
        <div class="empty-inline-action">
          <el-button type="primary" @click="router.push('/projects')">去项目列表</el-button>
        </div>
      </EmptyBlock>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>结果文本预览</h3>
          <p>复制后可直接用于内部回溯和汇报记录。</p>
        </div>
      </div>
      <el-input :model-value="historyText" type="textarea" :rows="12" readonly />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import { getBrokers } from "../../api/brokers";
import { getDashboardProjects } from "../../api/dashboard";
import { getHistoryLogs } from "../../api/history";
import EmptyBlock from "../../components/EmptyBlock.vue";
import type { BrokerSummary, DashboardProject, HistoryLogItem } from "../../types/models";

const router = useRouter();
const brokers = ref<BrokerSummary[]>([]);
const projects = ref<DashboardProject[]>([]);
const historyLogs = ref<HistoryLogItem[]>([]);
const dateRange = ref<string[]>([]);

const filters = reactive<{
  broker_id?: number;
  project_id?: number;
  keyword: string;
}>({
  broker_id: undefined,
  project_id: undefined,
  keyword: ""
});

const filteredProjects = computed(() => {
  if (!filters.broker_id) {
    return projects.value;
  }

  return projects.value.filter((item) => item.brokerId === filters.broker_id);
});

const historyText = computed(() => {
  return historyLogs.value
    .map(
      (item, index) =>
        `${index + 1}. [${item.logDate}] ${item.brokerName} / ${item.projectName}：${item.content}；下一步：${item.nextAction}`
    )
    .join("\n");
});

function handleBrokerChange() {
  filters.project_id = undefined;
}

function resetFilters() {
  filters.broker_id = undefined;
  filters.project_id = undefined;
  filters.keyword = "";
  dateRange.value = [];
  void loadHistory();
}

async function loadHistory() {
  historyLogs.value = await getHistoryLogs({
    broker_id: filters.broker_id,
    project_id: filters.project_id,
    start_date: dateRange.value[0],
    end_date: dateRange.value[1],
    keyword: filters.keyword
  });
}

async function copyHistoryText() {
  await navigator.clipboard.writeText(historyText.value);
  ElMessage.success("历史结果已复制");
}

function downloadHistoryCsv() {
  const header = ["记录时间", "券商", "项目", "类型", "跟进内容", "下一步动作"];
  const rows = historyLogs.value.map((item) => [
    item.logDate,
    item.brokerName,
    item.projectName,
    item.projectType,
    item.content,
    item.nextAction
  ]);

  const csv = [header, ...rows]
    .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(","))
    .join("\n");

  const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "项目历史.csv";
  link.click();
  URL.revokeObjectURL(url);
  ElMessage.success("项目历史 CSV 已导出");
}

onMounted(async () => {
  const [brokerData, projectData] = await Promise.all([getBrokers(), getDashboardProjects()]);
  brokers.value = brokerData;
  projects.value = projectData;
  await loadHistory();
});
</script>

<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">项目周报</p>
        <h2>先把周报结构稳定下来，再考虑更复杂的导出。</h2>
        <p>{{ report.summary }}</p>
      </div>
      <div>
        <div style="display: flex; gap: 12px; flex-wrap: wrap;">
          <el-button @click="downloadReportText">下载文本</el-button>
          <el-button type="primary" @click="copyReportText">复制汇报文本</el-button>
        </div>
      </div>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>筛选条件</h3>
          <p>支持按券商和负责人筛选周报内容。</p>
        </div>
        <div style="display: flex; gap: 12px; flex-wrap: wrap;">
          <el-button @click="resetFilters">重置筛选</el-button>
          <el-button type="primary" @click="loadReport">更新周报</el-button>
        </div>
      </div>
      <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px;">
        <el-form-item label="券商" style="margin-bottom: 0;">
          <el-select v-model="filters.broker_id" clearable placeholder="全部券商" style="width: 100%;">
            <el-option v-for="broker in brokers" :key="broker.id" :label="broker.name" :value="broker.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人" style="margin-bottom: 0;">
          <el-input v-model="filters.owner_name" placeholder="按负责人筛选" @keyup.enter="loadReport" />
        </el-form-item>
      </div>
    </section>

    <div v-if="hasReportContent" class="split-grid">
      <section class="section-card">
        <div class="section-title">
          <div>
            <h3>本周完成事项</h3>
          </div>
        </div>
        <ul class="bullet-panel">
          <li v-for="item in report.completed" :key="item">{{ item }}</li>
        </ul>
      </section>

      <section class="section-card">
        <div class="section-title">
          <div>
            <h3>下周计划事项</h3>
          </div>
        </div>
        <ul class="bullet-panel">
          <li v-for="item in report.nextWeek" :key="item">{{ item }}</li>
        </ul>
      </section>

      <section class="section-card">
        <div class="section-title">
          <div>
            <h3>逾期事项</h3>
          </div>
        </div>
        <ul class="bullet-panel">
          <li v-for="item in report.overdue" :key="item">{{ item }}</li>
        </ul>
      </section>

      <section class="section-card">
        <div class="section-title">
          <div>
            <h3>重点风险</h3>
          </div>
        </div>
        <ul class="bullet-panel">
          <li v-for="item in report.risks" :key="item">{{ item }}</li>
        </ul>
      </section>
    </div>

    <EmptyBlock
      v-else
      title="当前没有可生成的项目周报内容"
      description="可以先放宽筛选条件，或补充项目任务和跟进记录后再生成周报。"
    >
      <div class="empty-inline-action">
        <el-button type="primary" @click="loadReport">重新生成</el-button>
      </div>
    </EmptyBlock>

    <section v-if="hasReportContent" class="section-card">
      <div class="section-title">
        <div>
          <h3>需协调事项</h3>
        </div>
      </div>
      <ul class="bullet-panel">
        <li v-for="item in report.coordination" :key="item">{{ item }}</li>
      </ul>
    </section>

    <section v-if="hasReportContent" class="section-card">
      <div class="section-title">
        <div>
          <h3>汇报文本预览</h3>
          <p>复制后可直接发给领导或内部同步。</p>
        </div>
      </div>
      <el-input
        :model-value="reportText"
        type="textarea"
        :rows="14"
        readonly
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { getBrokers } from "../../api/brokers";
import { getWeeklyReportPreview } from "../../api/reports";
import EmptyBlock from "../../components/EmptyBlock.vue";
import type { BrokerSummary, WeeklyReport } from "../../types/models";

const brokers = ref<BrokerSummary[]>([]);
const report = ref<WeeklyReport>({
  summary: "",
  completed: [],
  nextWeek: [],
  overdue: [],
  risks: [],
  coordination: []
});
const filters = ref<{
  broker_id?: number;
  owner_name: string;
}>({
  broker_id: undefined,
  owner_name: ""
});

const hasReportContent = computed(() => {
  return (
    report.value.completed.length > 0 ||
    report.value.nextWeek.length > 0 ||
    report.value.overdue.length > 0 ||
    report.value.risks.length > 0 ||
    report.value.coordination.length > 0
  );
});

const reportText = computed(() => {
  const sections = [
    "【本周完成事项】",
    ...report.value.completed.map((item, index) => `${index + 1}. ${item}`),
    "",
    "【下周计划事项】",
    ...report.value.nextWeek.map((item, index) => `${index + 1}. ${item}`),
    "",
    "【逾期事项】",
    ...report.value.overdue.map((item, index) => `${index + 1}. ${item}`),
    "",
    "【重点风险】",
    ...report.value.risks.map((item, index) => `${index + 1}. ${item}`),
    "",
    "【需协调事项】",
    ...report.value.coordination.map((item, index) => `${index + 1}. ${item}`)
  ];

  return sections.join("\n");
});

async function copyReportText() {
  await navigator.clipboard.writeText(reportText.value);
  ElMessage.success("周报文本已复制");
}

function downloadReportText() {
  const blob = new Blob([reportText.value], { type: "text/plain;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "周报汇报文本.txt";
  link.click();
  URL.revokeObjectURL(url);
  ElMessage.success("周报文本已下载");
}

function resetFilters() {
  filters.value = {
    broker_id: undefined,
    owner_name: ""
  };
  void loadReport();
}

async function loadReport() {
  report.value = await getWeeklyReportPreview(filters.value);
}

onMounted(async () => {
  brokers.value = await getBrokers();
  await loadReport();
});
</script>

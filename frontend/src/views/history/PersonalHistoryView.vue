<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">个人历史</p>
        <h2>查看已完成的个人任务，不和项目历史混在一起。</h2>
        <p>这里专门保留你的个人任务完成记录，方便回顾自己的日常和长期事项。</p>
      </div>
      <div style="display: flex; gap: 12px; flex-wrap: wrap;">
        <el-button @click="resetFilters">重置筛选</el-button>
        <el-button @click="copyHistoryText">复制结果</el-button>
        <el-button @click="downloadHistoryCsv">导出 CSV</el-button>
      </div>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>筛选条件</h3>
          <p>支持按任务类型和关键词筛选个人历史。</p>
        </div>
      </div>
      <div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px;">
        <el-form-item label="类型" style="margin-bottom: 0;">
          <el-select v-model="filters.category" clearable placeholder="全部类型">
            <el-option label="每日" value="每日" />
            <el-option label="长期" value="长期" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词" style="margin-bottom: 0;">
          <el-input v-model="filters.keyword" placeholder="搜索任务标题或备注" @keyup.enter="loadHistory" />
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
          <h3>个人历史</h3>
          <p>当前共查询到 {{ historyItems.length }} 条已完成任务。</p>
        </div>
      </div>
      <el-table v-if="historyItems.length" :data="historyItems" stripe>
        <el-table-column prop="completedAt" label="完成时间" min-width="160" />
        <el-table-column prop="title" label="任务" min-width="220" />
        <el-table-column prop="category" label="类型" min-width="100" />
        <el-table-column prop="priority" label="优先级" min-width="100" />
        <el-table-column label="完成情况" min-width="260">
          <template #default="{ row }">
            <div class="table-multiline">{{ row.completionResult || "-" }}</div>
          </template>
        </el-table-column>
        <el-table-column label="备注" min-width="260">
          <template #default="{ row }">
            <div class="table-multiline">{{ row.note || "-" }}</div>
          </template>
        </el-table-column>
      </el-table>
      <EmptyBlock
        v-else
        title="还没有个人历史记录"
        description="完成个人任务后，这里会自动沉淀你的每日和长期任务记录。"
      >
        <div class="empty-inline-action">
          <el-button type="primary" @click="router.push('/personal')">去个人任务</el-button>
        </div>
      </EmptyBlock>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import { getPersonalHistory } from "../../api/personal";
import EmptyBlock from "../../components/EmptyBlock.vue";
import type { PersonalTaskItem } from "../../types/models";

const router = useRouter();
const historyItems = ref<PersonalTaskItem[]>([]);
const dateRange = ref<string[]>([]);
const filters = reactive<{ category?: string; keyword: string }>({
  category: undefined,
  keyword: ""
});

const historyText = computed(() => {
  return historyItems.value
    .map(
      (item, index) =>
        `${index + 1}. [${item.completedAt}] ${item.category} / ${item.title} / ${item.priority}：${item.completionResult || "已完成"}`
    )
    .join("\n");
});

function resetFilters() {
  filters.category = undefined;
  filters.keyword = "";
  dateRange.value = [];
  void loadHistory();
}

async function loadHistory() {
  historyItems.value = await getPersonalHistory({
    category: filters.category,
    keyword: filters.keyword,
    start_date: dateRange.value[0],
    end_date: dateRange.value[1]
  });
}

async function copyHistoryText() {
  await navigator.clipboard.writeText(historyText.value);
  ElMessage.success("个人历史已复制");
}

function downloadHistoryCsv() {
  const header = ["完成时间", "任务", "类型", "优先级", "完成情况", "备注"];
  const rows = historyItems.value.map((item) => [
    item.completedAt,
    item.title,
    item.category,
    item.priority,
    item.completionResult,
    item.note
  ]);
  const csv = [header, ...rows]
    .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(","))
    .join("\n");
  const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "个人历史.csv";
  link.click();
  URL.revokeObjectURL(url);
}

onMounted(async () => {
  await loadHistory();
});
</script>

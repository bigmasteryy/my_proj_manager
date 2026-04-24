<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">项目风险</p>
        <h2>把临期、逾期和高风险集中到一个处理台。</h2>
        <p>这里不是只看数据，而是为了让你快速完成处理动作。</p>
      </div>
    </section>

    <section class="section-card">
      <div class="table-toolbar">
        <el-radio-group v-model="activeType">
          <el-radio-button label="全部" />
          <el-radio-button label="临期" />
          <el-radio-button label="逾期" />
          <el-radio-button label="高风险" />
        </el-radio-group>
      </div>

      <el-table v-if="filteredReminders.length" :data="filteredReminders" stripe>
        <el-table-column prop="type" label="类型" min-width="100" />
        <el-table-column prop="brokerName" label="券商" min-width="120" />
        <el-table-column prop="projectName" label="项目" min-width="200" />
        <el-table-column prop="itemName" label="事项" min-width="160" />
        <el-table-column prop="deadline" label="截止时间" min-width="120" />
        <el-table-column label="等级" min-width="100">
          <template #default="{ row }">
            <StatusTag :label="row.level" />
          </template>
        </el-table-column>
        <el-table-column label="处理状态" min-width="120">
          <template #default="{ row }">
            <StatusTag :label="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="260" />
        <el-table-column label="操作" min-width="240" fixed="right">
          <template #default="{ row }">
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
              <el-button
                link
                type="primary"
                :disabled="row.status === '已处理'"
                @click="markHandled(row.id)"
              >
                标记已处理
              </el-button>
              <el-button
                link
                :disabled="row.status === '已忽略'"
                @click="markIgnored(row.id)"
              >
                忽略
              </el-button>
              <el-button link type="primary" @click="goProject(row.projectName)">查看项目</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <EmptyBlock
        v-else
        title="当前没有需要处理的项目风险"
        description="可以切换筛选类型看看，或回到项目列表继续跟进。"
      >
        <div class="empty-inline-action">
          <el-button type="primary" @click="router.push('/projects')">去项目列表</el-button>
        </div>
      </EmptyBlock>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import { getReminders, handleReminder, ignoreReminder } from "../../api/reminders";
import EmptyBlock from "../../components/EmptyBlock.vue";
import type { ReminderItem } from "../../types/models";
import StatusTag from "../../components/StatusTag.vue";

const router = useRouter();
const activeType = ref("全部");
const reminders = ref<ReminderItem[]>([]);

const filteredReminders = computed(() => {
  if (activeType.value === "全部") {
    return reminders.value;
  }

  return reminders.value.filter((item) => item.type === activeType.value);
});

async function loadReminders() {
  reminders.value = await getReminders();
}

async function markHandled(reminderId: number) {
  await handleReminder(reminderId);
  ElMessage.success("提醒已处理");
  await loadReminders();
}

async function markIgnored(reminderId: number) {
  await ignoreReminder(reminderId);
  ElMessage.success("提醒已忽略");
  await loadReminders();
}

function goProject(projectName: string) {
  if (projectName.includes("版本升级")) {
    router.push("/projects/1");
    return;
  }

  router.push("/projects/1");
}

onMounted(async () => {
  await loadReminders();
});
</script>

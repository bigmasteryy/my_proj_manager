<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">个人风险</p>
        <h2>这里只看个人任务风险，不混入项目风险。</h2>
        <p>个人任务里的逾期、临期和高优先级事项都会出现在这里。</p>
      </div>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>个人风险</h3>
          <p>当前共有 {{ risks.length }} 条个人风险事项。</p>
        </div>
      </div>
      <el-table v-if="risks.length" :data="risks" stripe>
        <el-table-column prop="type" label="类型" min-width="120" />
        <el-table-column prop="title" label="任务" min-width="220" />
        <el-table-column prop="category" label="分类" min-width="100" />
        <el-table-column prop="priority" label="优先级" min-width="100" />
        <el-table-column prop="plannedDate" label="计划日期" min-width="120" />
        <el-table-column label="备注" min-width="260">
          <template #default="{ row }">
            <div class="table-multiline">{{ row.note || "-" }}</div>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="180" fixed="right">
          <template #default="{ row }">
            <div style="display: flex; gap: 8px;">
              <el-button link type="success" @click="handleComplete(row.id)">完成任务</el-button>
              <el-button link type="primary" @click="router.push('/personal')">查看任务</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <EmptyBlock
        v-else
        title="当前没有个人风险"
        description="你的个人任务节奏比较稳定，暂时没有逾期、临期或高优先级风险项。"
      >
        <div class="empty-inline-action">
          <el-button type="primary" @click="router.push('/personal')">去个人任务</el-button>
        </div>
      </EmptyBlock>
    </section>

    <el-dialog
      v-model="completeDialogVisible"
      title="完成任务"
      width="620px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <el-form ref="completeFormRef" :model="completeForm" :rules="completeRules" label-width="110px">
        <el-form-item label="任务标题">
          <el-input :model-value="completingTaskTitle" disabled />
        </el-form-item>
        <el-form-item label="完成情况" prop="completion_result">
          <el-input
            v-model="completeForm.completion_result"
            type="textarea"
            :rows="4"
            placeholder="请填写完成结果、输出内容或补充说明"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="completeDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="completeSubmitting" @click="submitComplete">确认完成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import { useRouter } from "vue-router";
import { completePersonalTask, getPersonalRisks } from "../../api/personal";
import EmptyBlock from "../../components/EmptyBlock.vue";
import type { PersonalRiskItem, PersonalTaskCompletePayload } from "../../types/models";

const router = useRouter();
const risks = ref<PersonalRiskItem[]>([]);
const completeDialogVisible = ref(false);
const completeSubmitting = ref(false);
const completingTaskId = ref<number | null>(null);
const completingTaskTitle = ref("");
const completeFormRef = ref<FormInstance>();
const completeForm = reactive<PersonalTaskCompletePayload>({
  completion_result: ""
});
const completeRules: FormRules<PersonalTaskCompletePayload> = {
  completion_result: [{ required: true, message: "请输入完成情况", trigger: "blur" }]
};

async function loadRisks() {
  risks.value = await getPersonalRisks();
}

function handleComplete(taskId: number) {
  const current = risks.value.find((item) => item.id === taskId);
  completingTaskId.value = taskId;
  completingTaskTitle.value = current?.title || "";
  completeForm.completion_result = "";
  completeDialogVisible.value = true;
}

async function submitComplete() {
  const valid = await completeFormRef.value?.validate().catch(() => false);
  if (!valid || !completingTaskId.value) {
    return;
  }

  completeSubmitting.value = true;
  try {
    await completePersonalTask(completingTaskId.value, completeForm);
    completeDialogVisible.value = false;
    ElMessage.success("个人任务已完成，并记录了完成情况");
    await loadRisks();
  } finally {
    completeSubmitting.value = false;
  }
}

onMounted(async () => {
  await loadRisks();
});

watch(completeDialogVisible, (visible) => {
  if (!visible) {
    completingTaskId.value = null;
    completingTaskTitle.value = "";
    completeForm.completion_result = "";
  }
});
</script>

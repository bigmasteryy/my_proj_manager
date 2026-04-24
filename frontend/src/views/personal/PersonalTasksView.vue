<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">每日任务</p>
        <h2>先把今天要推进的事排清楚，再专注处理最重要的几项。</h2>
        <p>支持关联长期任务、按优先级筛选，并在当前页直接调整任务顺序。</p>
      </div>
      <div class="hero-actions">
        <el-button @click="handleResetDaily">重置每日任务</el-button>
        <el-button type="primary" @click="openCreateDialog">新增每日任务</el-button>
      </div>
    </section>

    <section class="compact-grid compact-grid-4">
      <article class="compact-card">
        <small>当前待办</small>
        <strong>{{ summary.total }}</strong>
      </article>
      <article class="compact-card">
        <small>高优先级</small>
        <strong>{{ summary.high }}</strong>
      </article>
      <article class="compact-card">
        <small>今日到期 / 逾期</small>
        <strong>{{ summary.due }}</strong>
      </article>
      <article class="compact-card">
        <small>已关联长期任务</small>
        <strong>{{ summary.linked }}</strong>
      </article>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>快速筛选</h3>
          <p>先缩小范围，再处理当下最需要关注的任务。</p>
        </div>
        <el-button link type="primary" @click="resetFilters">清空筛选</el-button>
      </div>
      <div class="filter-grid">
        <el-input
          v-model="filters.keyword"
          placeholder="搜索任务标题或备注"
          clearable
        />
        <el-select v-model="filters.priority" clearable placeholder="全部优先级">
          <el-option label="高" value="高" />
          <el-option label="中" value="中" />
          <el-option label="低" value="低" />
        </el-select>
        <el-select v-model="filters.parentTaskId" clearable placeholder="全部长期任务">
          <el-option
            v-for="item in longTermOptions"
            :key="item.id"
            :label="item.title"
            :value="item.id"
          />
        </el-select>
        <el-select v-model="filters.dateScope" clearable placeholder="全部日期范围">
          <el-option label="今日到期 / 逾期" value="due" />
          <el-option label="未来 3 天内" value="soon" />
          <el-option label="未设置日期" value="undated" />
        </el-select>
      </div>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>每日任务列表</h3>
          <p>
            当前显示 {{ filteredTasks.length }} 条任务
            <span v-if="hasActiveFilters">，已按筛选条件收窄范围</span>
            <span v-else>，可直接选中任务调整顺序</span>
          </p>
        </div>
        <div class="hero-actions compact">
          <div class="selection-hint" v-if="selectedTask">
            已选中：<strong>{{ selectedTask.title }}</strong>
          </div>
          <el-button
            :disabled="!canMoveSelectedTask || isSelectedTaskFirst"
            @click="moveTask(-1)"
          >
            上移
          </el-button>
          <el-button
            :disabled="!canMoveSelectedTask || isSelectedTaskLast"
            @click="moveTask(1)"
          >
            下移
          </el-button>
        </div>
      </div>

      <el-table
        v-if="filteredTasks.length"
        :data="filteredTasks"
        stripe
        highlight-current-row
        row-key="id"
        @current-change="handleCurrentChange"
      >
        <el-table-column prop="title" label="任务" min-width="220" />
        <el-table-column label="所属长期任务" min-width="180">
          <template #default="{ row }">
            <el-button
              v-if="row.parentTaskId"
              link
              type="primary"
              @click="router.push(`/personal/long-term?taskId=${row.parentTaskId}`)"
            >
              {{ row.parentTaskTitle || "查看长期任务" }}
            </el-button>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="关联进度" min-width="180">
          <template #default="{ row }">
            <div v-if="row.parentTaskId && getParentTaskMeta(row.parentTaskId)" class="progress-cell">
              <el-progress
                :percentage="getParentTaskMeta(row.parentTaskId)?.progressPercent || 0"
                :stroke-width="8"
                :show-text="false"
              />
              <span class="compact-note">
                {{ getParentTaskMeta(row.parentTaskId)?.completedChildCount || 0 }}/{{ getParentTaskMeta(row.parentTaskId)?.childCount || 0 }}
              </span>
            </div>
            <span v-else class="compact-note">独立任务</span>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" min-width="100" />
        <el-table-column prop="plannedDate" label="计划日期" min-width="120" />
        <el-table-column label="备注" min-width="260">
          <template #default="{ row }">
            <div class="table-multiline">{{ row.note || "-" }}</div>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="240" fixed="right">
          <template #default="{ row }">
            <div class="action-row">
              <el-button link type="success" @click="handleComplete(row.id, row.title)">完成</el-button>
              <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
              <el-button link type="danger" @click="handleDelete(row.id)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <EmptyBlock
        v-else-if="tasks.length"
        title="当前筛选条件下没有匹配任务"
        description="可以放宽筛选条件，或者直接新增一条新的每日任务。"
      >
        <div class="empty-inline-action">
          <el-button @click="resetFilters">清空筛选</el-button>
          <el-button type="primary" @click="openCreateDialog">新增每日任务</el-button>
        </div>
      </EmptyBlock>

      <EmptyBlock
        v-else
        title="当前还没有每日任务"
        description="可以先新增一条每日任务，或者从长期任务里拆分一条子任务到今天执行。"
      >
        <div class="empty-inline-action">
          <el-button type="primary" @click="openCreateDialog">新增每日任务</el-button>
        </div>
      </EmptyBlock>
    </section>

    <el-dialog
      v-model="dialogVisible"
      :title="editingTaskId ? '编辑每日任务' : '新增每日任务'"
      width="620px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :before-close="handleDialogBeforeClose"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="关联长期任务">
          <el-select v-model="form.parent_task_id" clearable placeholder="可选" style="width: 100%;">
            <el-option
              v-for="item in longTermOptions"
              :key="item.id"
              :label="item.title"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="form.priority" style="width: 100%;">
            <el-option label="高" value="高" />
            <el-option label="中" value="中" />
            <el-option label="低" value="低" />
          </el-select>
        </el-form-item>
        <el-form-item label="计划日期">
          <el-date-picker
            v-model="form.planned_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="requestCloseDialog">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSave">保存任务</el-button>
      </template>
    </el-dialog>

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
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from "element-plus";
import { useRouter } from "vue-router";

import {
  completePersonalTask,
  createPersonalTask,
  deletePersonalTask,
  getPersonalTasks,
  resetDailyTasks,
  sortPersonalTasks,
  updatePersonalTask
} from "../../api/personal";
import EmptyBlock from "../../components/EmptyBlock.vue";
import type {
  PersonalTaskCompletePayload,
  PersonalTaskCreatePayload,
  PersonalTaskItem
} from "../../types/models";

const router = useRouter();

const tasks = ref<PersonalTaskItem[]>([]);
const longTermOptions = ref<PersonalTaskItem[]>([]);
const selectedTaskId = ref<number | null>(null);

const dialogVisible = ref(false);
const submitting = ref(false);
const editingTaskId = ref<number | null>(null);
const completingTaskId = ref<number | null>(null);
const completingTaskTitle = ref("");
const completeDialogVisible = ref(false);
const completeSubmitting = ref(false);
const formSnapshot = ref("");

const formRef = ref<FormInstance>();
const completeFormRef = ref<FormInstance>();

const filters = reactive({
  keyword: "",
  priority: "",
  dateScope: "",
  parentTaskId: null as number | null
});

const form = reactive<PersonalTaskCreatePayload>({
  title: "",
  category: "每日",
  priority: "中",
  note: "",
  planned_date: "",
  parent_task_id: null
});

const completeForm = reactive<PersonalTaskCompletePayload>({
  completion_result: ""
});

const rules: FormRules<PersonalTaskCreatePayload> = {
  title: [{ required: true, message: "请输入任务标题", trigger: "blur" }],
  priority: [{ required: true, message: "请选择优先级", trigger: "change" }]
};

const completeRules: FormRules<PersonalTaskCompletePayload> = {
  completion_result: [{ required: true, message: "请输入完成情况", trigger: "blur" }]
};

function createSnapshot<T>(value: T) {
  return JSON.stringify(value);
}

const today = computed(() => new Date().toISOString().slice(0, 10));

const summary = computed(() => ({
  total: tasks.value.length,
  high: tasks.value.filter((item) => item.priority === "高").length,
  due: tasks.value.filter((item) => item.plannedDate && item.plannedDate <= today.value).length,
  linked: tasks.value.filter((item) => Boolean(item.parentTaskId)).length
}));

const longTaskMetaMap = computed(() => {
  const map = new Map<number, { childCount: number; completedChildCount: number; progressPercent: number }>();
  for (const item of longTermOptions.value) {
    const progressPercent = item.childCount
      ? Math.round((item.completedChildCount / item.childCount) * 100)
      : 0;
    map.set(item.id, {
      childCount: item.childCount,
      completedChildCount: item.completedChildCount,
      progressPercent
    });
  }
  return map;
});

const hasActiveFilters = computed(() =>
  Boolean(filters.keyword || filters.priority || filters.dateScope || filters.parentTaskId)
);

const filteredTasks = computed(() => {
  return tasks.value.filter((item) => {
    const keyword = filters.keyword.trim().toLowerCase();
    const matchesKeyword = !keyword
      || item.title.toLowerCase().includes(keyword)
      || item.note.toLowerCase().includes(keyword);
    const matchesPriority = !filters.priority || item.priority === filters.priority;
    const matchesParent = !filters.parentTaskId || item.parentTaskId === filters.parentTaskId;

    let matchesDateScope = true;
    if (filters.dateScope === "due") {
      matchesDateScope = Boolean(item.plannedDate) && item.plannedDate <= today.value;
    } else if (filters.dateScope === "soon") {
      matchesDateScope = Boolean(item.plannedDate)
        && item.plannedDate > today.value
        && item.plannedDate <= plusDays(today.value, 3);
    } else if (filters.dateScope === "undated") {
      matchesDateScope = !item.plannedDate;
    }

    return matchesKeyword && matchesPriority && matchesParent && matchesDateScope;
  });
});

const selectedTask = computed(() => tasks.value.find((item) => item.id === selectedTaskId.value) || null);
const selectedTaskIndex = computed(() => tasks.value.findIndex((item) => item.id === selectedTaskId.value));
const canMoveSelectedTask = computed(() => Boolean(selectedTask.value) && !hasActiveFilters.value);
const isSelectedTaskFirst = computed(() => selectedTaskIndex.value <= 0);
const isSelectedTaskLast = computed(
  () => selectedTaskIndex.value < 0 || selectedTaskIndex.value >= tasks.value.length - 1
);

function plusDays(baseDate: string, days: number) {
  const date = new Date(baseDate);
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
}

function getParentTaskMeta(parentTaskId: number | null) {
  if (!parentTaskId) {
    return null;
  }
  return longTaskMetaMap.value.get(parentTaskId) || null;
}

async function confirmDiscardChanges() {
  const dirty = createSnapshot(form) !== formSnapshot.value;
  if (!dirty) {
    return true;
  }

  try {
    await ElMessageBox.confirm(
      "任务内容尚未保存，确定要关闭吗？",
      "放弃未保存内容",
      {
        type: "warning",
        confirmButtonText: "放弃并关闭",
        cancelButtonText: "继续编辑"
      }
    );
    return true;
  } catch {
    return false;
  }
}

function resetFilters() {
  filters.keyword = "";
  filters.priority = "";
  filters.dateScope = "";
  filters.parentTaskId = null;
}

function resetForm() {
  editingTaskId.value = null;
  form.title = "";
  form.category = "每日";
  form.priority = "中";
  form.note = "";
  form.planned_date = "";
  form.parent_task_id = null;
}

function openCreateDialog() {
  resetForm();
  formSnapshot.value = createSnapshot(form);
  dialogVisible.value = true;
}

function openEditDialog(task: PersonalTaskItem) {
  editingTaskId.value = task.id;
  form.title = task.title;
  form.category = "每日";
  form.priority = task.priority;
  form.note = task.note;
  form.planned_date = task.plannedDate || "";
  form.parent_task_id = task.parentTaskId;
  formSnapshot.value = createSnapshot(form);
  dialogVisible.value = true;
}

async function requestCloseDialog() {
  const shouldClose = await confirmDiscardChanges();
  if (shouldClose) {
    dialogVisible.value = false;
  }
}

async function handleDialogBeforeClose(done: () => void) {
  const shouldClose = await confirmDiscardChanges();
  if (shouldClose) {
    done();
  }
}

async function loadTasks() {
  const [dailyTasks, longTasks] = await Promise.all([
    getPersonalTasks("每日"),
    getPersonalTasks("长期")
  ]);
  tasks.value = dailyTasks;
  longTermOptions.value = longTasks;

  if (selectedTaskId.value) {
    const exists = dailyTasks.some((item) => item.id === selectedTaskId.value);
    if (!exists) {
      selectedTaskId.value = null;
    }
  }
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  submitting.value = true;
  try {
    if (editingTaskId.value) {
      await updatePersonalTask(editingTaskId.value, form);
      ElMessage.success("每日任务已更新");
    } else {
      await createPersonalTask(form);
      ElMessage.success("每日任务已新增");
    }
    dialogVisible.value = false;
    await loadTasks();
  } finally {
    submitting.value = false;
  }
}

function handleComplete(taskId: number, title: string) {
  completingTaskId.value = taskId;
  completingTaskTitle.value = title;
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
    ElMessage.success("任务已完成，并已记录完成时间和完成情况");
    await loadTasks();
  } finally {
    completeSubmitting.value = false;
  }
}

async function handleDelete(taskId: number) {
  try {
    await ElMessageBox.confirm(
      "确认删除这条每日任务吗？删除后不会进入个人历史，且无法恢复。",
      "删除确认",
      {
        type: "warning",
        confirmButtonText: "确认删除",
        cancelButtonText: "取消"
      }
    );
  } catch {
    return;
  }

  await deletePersonalTask(taskId);
  ElMessage.success("每日任务已删除");
  await loadTasks();
}

function handleCurrentChange(task: PersonalTaskItem | undefined) {
  selectedTaskId.value = task?.id ?? null;
}

async function moveTask(direction: -1 | 1) {
  if (!selectedTask.value || hasActiveFilters.value) {
    return;
  }

  const index = tasks.value.findIndex((item) => item.id === selectedTask.value?.id);
  const nextIndex = index + direction;
  if (index < 0 || nextIndex < 0 || nextIndex >= tasks.value.length) {
    return;
  }

  const reordered = [...tasks.value];
  const current = reordered[index];
  reordered[index] = reordered[nextIndex];
  reordered[nextIndex] = current;
  tasks.value = reordered;

  await sortPersonalTasks(reordered.map((item) => item.id));
  selectedTaskId.value = current.id;
  ElMessage.success("任务顺序已更新");
}

async function handleResetDaily() {
  try {
    await ElMessageBox.confirm(
      "确认将未完成的每日任务重置为待办状态吗？已完成任务不会受影响。",
      "重置每日任务",
      {
        type: "warning",
        confirmButtonText: "确认重置",
        cancelButtonText: "取消"
      }
    );
  } catch {
    return;
  }

  await resetDailyTasks();
  ElMessage.success("每日任务已重置为待办");
  await loadTasks();
}

onMounted(async () => {
  await loadTasks();
});

watch(dialogVisible, (visible) => {
  if (!visible) {
    resetForm();
    formSnapshot.value = "";
  }
});

watch(completeDialogVisible, (visible) => {
  if (!visible) {
    completingTaskId.value = null;
    completingTaskTitle.value = "";
    completeForm.completion_result = "";
  }
});
</script>

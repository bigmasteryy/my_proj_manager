<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">长期任务</p>
        <h2>沉淀需要持续推进的事项，再拆成每日子任务去执行。</h2>
        <p>选中一条长期任务后，可以直接查看它的进度、备注和每日子任务明细。</p>
      </div>
      <div class="hero-actions">
        <el-button :disabled="!selectedTask" @click="openCreateDailyDialog(selectedTask)">增加每日任务</el-button>
        <el-button type="primary" @click="openCreateLongTaskDialog">新增长期任务</el-button>
      </div>
    </section>

    <section class="compact-grid compact-grid-4">
      <article class="compact-card">
        <small>长期任务</small>
        <strong>{{ longTasks.length }}</strong>
      </article>
      <article class="compact-card">
        <small>高优先级</small>
        <strong>{{ highPriorityCount }}</strong>
      </article>
      <article class="compact-card">
        <small>进行中子任务</small>
        <strong>{{ activeSubtaskCount }}</strong>
      </article>
      <article class="compact-card">
        <small>当前选中进度</small>
        <strong>{{ selectedProgressPercent }}%</strong>
      </article>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>快速筛选</h3>
          <p>先找到正在推进或最需要跟进的长期任务，再看子任务明细。</p>
        </div>
        <el-button link type="primary" @click="resetFilters">清空筛选</el-button>
      </div>
      <div class="filter-grid">
        <el-input
          v-model="filters.keyword"
          placeholder="搜索长期任务标题或备注"
          clearable
        />
        <el-select v-model="filters.priority" clearable placeholder="全部优先级">
          <el-option label="高" value="高" />
          <el-option label="中" value="中" />
          <el-option label="低" value="低" />
        </el-select>
        <el-select v-model="filters.progress" clearable placeholder="全部进度">
          <el-option label="未拆分子任务" value="empty" />
          <el-option label="有进行中子任务" value="active" />
          <el-option label="子任务已全部完成" value="done" />
        </el-select>
      </div>
    </section>

    <section class="stack">
      <section class="section-card">
        <div class="section-title">
          <div>
            <h3>长期任务列表</h3>
            <p>当前显示 {{ filteredLongTasks.length }} 条长期任务。</p>
          </div>
        </div>

        <el-table
          v-if="filteredLongTasks.length"
          :data="filteredLongTasks"
          stripe
          highlight-current-row
          row-key="id"
          @current-change="handleTaskSelect"
        >
          <el-table-column prop="title" label="任务" min-width="220" />
          <el-table-column prop="priority" label="优先级" min-width="90" />
          <el-table-column label="子任务数" min-width="90">
            <template #default="{ row }">
              {{ row.childCount }}
            </template>
          </el-table-column>
          <el-table-column label="进度" min-width="180">
            <template #default="{ row }">
              <div class="progress-cell">
                <el-progress
                  :percentage="getProgressPercent(row)"
                  :stroke-width="8"
                  :show-text="false"
                />
                <span class="compact-note">{{ row.completedChildCount }}/{{ row.childCount || 0 }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="备注" min-width="240">
            <template #default="{ row }">
              <div class="table-multiline">{{ row.note || "-" }}</div>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="260" fixed="right">
            <template #default="{ row }">
              <div class="action-row">
                <el-button link type="primary" @click="handleTaskSelect(row)">查看明细</el-button>
                <el-button link type="success" @click="handleComplete(row.id, row.title)">完成</el-button>
                <el-button link type="primary" @click="openEditLongTaskDialog(row)">编辑</el-button>
                <el-button link type="warning" @click="openCreateDailyDialog(row)">增加每日任务</el-button>
                <el-button link type="danger" @click="handleDeleteTask(row.id, '长期任务')">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <EmptyBlock
          v-else-if="longTasks.length"
          title="当前筛选条件下没有匹配的长期任务"
          description="可以放宽筛选条件，或者直接新增一条长期任务。"
        >
          <div class="empty-inline-action">
            <el-button @click="resetFilters">清空筛选</el-button>
            <el-button type="primary" @click="openCreateLongTaskDialog">新增长期任务</el-button>
          </div>
        </EmptyBlock>

        <EmptyBlock
          v-else
          title="当前还没有长期任务"
          description="可以先新增一条长期任务，再把它拆成每日子任务去推进。"
        >
          <div class="empty-inline-action">
            <el-button type="primary" @click="openCreateLongTaskDialog">新增长期任务</el-button>
          </div>
        </EmptyBlock>
      </section>

      <section class="section-card">
        <div class="section-title">
          <div>
            <h3>任务明细</h3>
            <p v-if="selectedTask">围绕当前选中的长期任务查看进度、备注和子任务。</p>
            <p v-else>请选择一条长期任务查看详细信息。</p>
          </div>
          <el-button v-if="selectedTask" type="primary" @click="openCreateDailyDialog(selectedTask)">增加每日任务</el-button>
        </div>

        <template v-if="selectedTask">
          <div class="detail-shell">
            <div class="detail-header">
              <div>
                <h3 style="margin: 0 0 6px;">{{ selectedTask.title }}</h3>
                <p class="compact-note" style="margin: 0;">
                  优先级：{{ selectedTask.priority }} · 子任务 {{ selectedTask.completedChildCount }}/{{ selectedTask.childCount || 0 }}
                </p>
              </div>
              <div class="hero-actions compact">
                <el-button @click="openEditLongTaskDialog(selectedTask)">编辑长期任务</el-button>
                <el-button type="primary" @click="openCreateDailyDialog(selectedTask)">增加每日任务</el-button>
              </div>
            </div>

            <div class="progress-block">
              <div class="progress-meta">
                <span>当前推进进度</span>
                <strong>{{ selectedProgressPercent }}%</strong>
              </div>
              <el-progress :percentage="selectedProgressPercent" :stroke-width="10" />
            </div>

            <div class="compact-grid">
              <article class="compact-card">
                <small>总子任务</small>
                <strong>{{ selectedTask.childCount }}</strong>
              </article>
              <article class="compact-card">
                <small>已完成子任务</small>
                <strong>{{ selectedTask.completedChildCount }}</strong>
              </article>
              <article class="compact-card">
                <small>进行中子任务</small>
                <strong>{{ subtasks.length }}</strong>
              </article>
            </div>

            <div class="note-panel">
              <small>备注</small>
              <div class="table-multiline">{{ selectedTask.note || "当前没有补充备注。" }}</div>
            </div>

            <section class="subtask-block">
              <div class="section-title section-title-tight">
                <div>
                  <h3>进行中子任务</h3>
                  <p>这些是当前还需要继续推进的每日任务。</p>
                </div>
              </div>

              <el-table v-if="subtasks.length" :data="subtasks" stripe>
                <el-table-column prop="title" label="子任务" min-width="220" />
                <el-table-column prop="priority" label="优先级" min-width="90" />
                <el-table-column prop="plannedDate" label="计划日期" min-width="120" />
                <el-table-column label="备注" min-width="240">
                  <template #default="{ row }">
                    <div class="table-multiline">{{ row.note || "-" }}</div>
                  </template>
                </el-table-column>
                <el-table-column label="操作" min-width="220" fixed="right">
                  <template #default="{ row }">
                    <div class="action-row">
                      <el-button link type="success" @click="handleComplete(row.id, row.title)">完成</el-button>
                      <el-button link type="primary" @click="openEditDailyDialog(row)">编辑</el-button>
                      <el-button link type="danger" @click="handleDeleteTask(row.id, '每日子任务')">删除</el-button>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
              <EmptyBlock
                v-else
                compact
                title="当前还没有进行中的子任务"
                description="可以先为这条长期任务拆分一条新的每日任务。"
              >
                <div class="empty-inline-action">
                  <el-button type="primary" @click="openCreateDailyDialog(selectedTask)">增加每日任务</el-button>
                </div>
              </EmptyBlock>
            </section>

            <section class="subtask-block">
              <div class="section-title section-title-tight">
                <div>
                  <h3>已完成子任务</h3>
                  <p>这里保留已完成子任务的时间和完成说明，方便回看推进过程。</p>
                </div>
              </div>

              <el-table v-if="completedSubtasks.length" :data="completedSubtasks" stripe>
                <el-table-column prop="title" label="子任务" min-width="200" />
                <el-table-column prop="completedAt" label="完成时间" min-width="160" />
                <el-table-column label="完成情况" min-width="240">
                  <template #default="{ row }">
                    <div class="table-multiline">{{ row.completionResult || "-" }}</div>
                  </template>
                </el-table-column>
                <el-table-column label="备注" min-width="220">
                  <template #default="{ row }">
                    <div class="table-multiline">{{ row.note || "-" }}</div>
                  </template>
                </el-table-column>
              </el-table>
              <EmptyBlock
                v-else
                compact
                title="暂时没有已完成子任务"
                description="完成子任务后，这里会自动沉淀完成记录。"
              />
            </section>
          </div>
        </template>

        <EmptyBlock
          v-else
          compact
          title="请选择一条长期任务"
          description="选中长期任务后，这里会显示它对应的子任务明细和推进进度。"
        />
      </section>
    </section>

    <el-dialog
      v-model="longTaskDialogVisible"
      :title="editingLongTaskId ? '编辑长期任务' : '新增长期任务'"
      width="620px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :before-close="handleLongTaskDialogBeforeClose"
    >
      <el-form ref="longTaskFormRef" :model="longTaskForm" :rules="taskRules" label-width="110px">
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="longTaskForm.title" />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="longTaskForm.priority" style="width: 100%;">
            <el-option label="高" value="高" />
            <el-option label="中" value="中" />
            <el-option label="低" value="低" />
          </el-select>
        </el-form-item>
        <el-form-item label="计划日期">
          <el-date-picker
            v-model="longTaskForm.planned_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="longTaskForm.note" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="requestCloseLongTaskDialog">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSaveLongTask">保存长期任务</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="dailyTaskDialogVisible"
      :title="editingDailyTaskId ? '编辑每日子任务' : '新增每日子任务'"
      width="620px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :before-close="handleDailyTaskDialogBeforeClose"
    >
      <el-form ref="dailyTaskFormRef" :model="dailyTaskForm" :rules="taskRules" label-width="110px">
        <el-form-item label="所属长期任务">
          <el-input :model-value="selectedTask?.title || ''" disabled />
        </el-form-item>
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="dailyTaskForm.title" />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="dailyTaskForm.priority" style="width: 100%;">
            <el-option label="高" value="高" />
            <el-option label="中" value="中" />
            <el-option label="低" value="低" />
          </el-select>
        </el-form-item>
        <el-form-item label="计划日期">
          <el-date-picker
            v-model="dailyTaskForm.planned_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="dailyTaskForm.note" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="requestCloseDailyTaskDialog">取消</el-button>
        <el-button type="primary" :loading="dailySubmitting" @click="handleSaveDailyTask">保存每日任务</el-button>
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
import { useRoute } from "vue-router";

import {
  completePersonalTask,
  createPersonalTask,
  deletePersonalTask,
  getPersonalHistory,
  getPersonalTasks,
  updatePersonalTask
} from "../../api/personal";
import EmptyBlock from "../../components/EmptyBlock.vue";
import type {
  PersonalTaskCompletePayload,
  PersonalTaskCreatePayload,
  PersonalTaskItem
} from "../../types/models";

const route = useRoute();

const longTasks = ref<PersonalTaskItem[]>([]);
const subtasks = ref<PersonalTaskItem[]>([]);
const completedSubtasks = ref<PersonalTaskItem[]>([]);
const selectedTask = ref<PersonalTaskItem | null>(null);

const longTaskDialogVisible = ref(false);
const dailyTaskDialogVisible = ref(false);
const completeDialogVisible = ref(false);
const submitting = ref(false);
const dailySubmitting = ref(false);
const completeSubmitting = ref(false);

const editingLongTaskId = ref<number | null>(null);
const editingDailyTaskId = ref<number | null>(null);
const completingTaskId = ref<number | null>(null);
const completingTaskTitle = ref("");

const longTaskFormRef = ref<FormInstance>();
const dailyTaskFormRef = ref<FormInstance>();
const completeFormRef = ref<FormInstance>();
const longTaskSnapshot = ref("");
const dailyTaskSnapshot = ref("");

const filters = reactive({
  keyword: "",
  priority: "",
  progress: ""
});

const longTaskForm = reactive<PersonalTaskCreatePayload>({
  title: "",
  category: "长期",
  priority: "中",
  note: "",
  planned_date: "",
  parent_task_id: null
});

const dailyTaskForm = reactive<PersonalTaskCreatePayload>({
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

const taskRules: FormRules<PersonalTaskCreatePayload> = {
  title: [{ required: true, message: "请输入任务标题", trigger: "blur" }],
  priority: [{ required: true, message: "请选择优先级", trigger: "change" }]
};

const completeRules: FormRules<PersonalTaskCompletePayload> = {
  completion_result: [{ required: true, message: "请输入完成情况", trigger: "blur" }]
};

const filteredLongTasks = computed(() => {
  return longTasks.value.filter((item) => {
    const keyword = filters.keyword.trim().toLowerCase();
    const matchesKeyword = !keyword
      || item.title.toLowerCase().includes(keyword)
      || item.note.toLowerCase().includes(keyword);
    const matchesPriority = !filters.priority || item.priority === filters.priority;

    let matchesProgress = true;
    if (filters.progress === "empty") {
      matchesProgress = item.childCount === 0;
    } else if (filters.progress === "active") {
      matchesProgress = item.childCount > 0 && item.completedChildCount < item.childCount;
    } else if (filters.progress === "done") {
      matchesProgress = item.childCount > 0 && item.completedChildCount === item.childCount;
    }

    return matchesKeyword && matchesPriority && matchesProgress;
  });
});

const selectedProgressPercent = computed(() => getProgressPercent(selectedTask.value));
const highPriorityCount = computed(() => longTasks.value.filter((item) => item.priority === "高").length);
const activeSubtaskCount = computed(() => selectedTask.value ? subtasks.value.length : 0);

function getProgressPercent(task?: PersonalTaskItem | null) {
  if (!task || !task.childCount) {
    return 0;
  }
  return Math.round((task.completedChildCount / task.childCount) * 100);
}

function createSnapshot<T>(value: T) {
  return JSON.stringify(value);
}

function resetFilters() {
  filters.keyword = "";
  filters.priority = "";
  filters.progress = "";
}

async function confirmDiscardChanges(label: string, dirty: boolean) {
  if (!dirty) {
    return true;
  }

  try {
    await ElMessageBox.confirm(
      `${label}内容尚未保存，确定要关闭吗？`,
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

function resetLongTaskForm() {
  editingLongTaskId.value = null;
  longTaskForm.title = "";
  longTaskForm.category = "长期";
  longTaskForm.priority = "中";
  longTaskForm.note = "";
  longTaskForm.planned_date = "";
  longTaskForm.parent_task_id = null;
}

function resetDailyTaskForm() {
  editingDailyTaskId.value = null;
  dailyTaskForm.title = "";
  dailyTaskForm.category = "每日";
  dailyTaskForm.priority = "中";
  dailyTaskForm.note = "";
  dailyTaskForm.planned_date = "";
  dailyTaskForm.parent_task_id = selectedTask.value?.id ?? null;
}

async function loadLongTasks() {
  longTasks.value = await getPersonalTasks("长期");

  const queryTaskId = Number(route.query.taskId || 0);
  if (queryTaskId) {
    selectedTask.value = longTasks.value.find((item) => item.id === queryTaskId) || null;
  } else if (selectedTask.value) {
    selectedTask.value = longTasks.value.find((item) => item.id === selectedTask.value?.id) || null;
  }

  if (!selectedTask.value && longTasks.value.length) {
    selectedTask.value = longTasks.value[0];
  }
}

async function loadSubtasks() {
  if (!selectedTask.value) {
    subtasks.value = [];
    completedSubtasks.value = [];
    return;
  }

  subtasks.value = await getPersonalTasks({
    category: "每日",
    parent_task_id: selectedTask.value.id
  });
  completedSubtasks.value = await getPersonalHistory({
    category: "每日",
    parent_task_id: selectedTask.value.id
  });
}

async function refreshData() {
  await loadLongTasks();
  await loadSubtasks();
}

function handleTaskSelect(task: PersonalTaskItem | undefined) {
  selectedTask.value = task || null;
  void loadSubtasks();
}

function openCreateLongTaskDialog() {
  resetLongTaskForm();
  longTaskSnapshot.value = createSnapshot(longTaskForm);
  longTaskDialogVisible.value = true;
}

function openEditLongTaskDialog(task: PersonalTaskItem) {
  editingLongTaskId.value = task.id;
  longTaskForm.title = task.title;
  longTaskForm.category = "长期";
  longTaskForm.priority = task.priority;
  longTaskForm.note = task.note;
  longTaskForm.planned_date = task.plannedDate || "";
  longTaskForm.parent_task_id = null;
  longTaskSnapshot.value = createSnapshot(longTaskForm);
  longTaskDialogVisible.value = true;
}

function openCreateDailyDialog(task?: PersonalTaskItem | null) {
  if (task) {
    selectedTask.value = task;
  }
  if (!selectedTask.value) {
    ElMessage.warning("请先选择一条长期任务");
    return;
  }

  resetDailyTaskForm();
  dailyTaskSnapshot.value = createSnapshot(dailyTaskForm);
  dailyTaskDialogVisible.value = true;
}

function openEditDailyDialog(task: PersonalTaskItem) {
  editingDailyTaskId.value = task.id;
  dailyTaskForm.title = task.title;
  dailyTaskForm.category = "每日";
  dailyTaskForm.priority = task.priority;
  dailyTaskForm.note = task.note;
  dailyTaskForm.planned_date = task.plannedDate || "";
  dailyTaskForm.parent_task_id = task.parentTaskId;
  dailyTaskSnapshot.value = createSnapshot(dailyTaskForm);
  dailyTaskDialogVisible.value = true;
}

async function requestCloseLongTaskDialog() {
  const shouldClose = await confirmDiscardChanges(
    "长期任务表单",
    createSnapshot(longTaskForm) !== longTaskSnapshot.value
  );
  if (shouldClose) {
    longTaskDialogVisible.value = false;
  }
}

async function handleLongTaskDialogBeforeClose(done: () => void) {
  const shouldClose = await confirmDiscardChanges(
    "长期任务表单",
    createSnapshot(longTaskForm) !== longTaskSnapshot.value
  );
  if (shouldClose) {
    done();
  }
}

async function requestCloseDailyTaskDialog() {
  const shouldClose = await confirmDiscardChanges(
    "每日任务表单",
    createSnapshot(dailyTaskForm) !== dailyTaskSnapshot.value
  );
  if (shouldClose) {
    dailyTaskDialogVisible.value = false;
  }
}

async function handleDailyTaskDialogBeforeClose(done: () => void) {
  const shouldClose = await confirmDiscardChanges(
    "每日任务表单",
    createSnapshot(dailyTaskForm) !== dailyTaskSnapshot.value
  );
  if (shouldClose) {
    done();
  }
}

async function handleSaveLongTask() {
  const valid = await longTaskFormRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  submitting.value = true;
  try {
    if (editingLongTaskId.value) {
      await updatePersonalTask(editingLongTaskId.value, longTaskForm);
      ElMessage.success("长期任务已更新");
    } else {
      await createPersonalTask(longTaskForm);
      ElMessage.success("长期任务已新增");
    }
    longTaskDialogVisible.value = false;
    await refreshData();
  } finally {
    submitting.value = false;
  }
}

async function handleSaveDailyTask() {
  const valid = await dailyTaskFormRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  dailySubmitting.value = true;
  try {
    if (editingDailyTaskId.value) {
      await updatePersonalTask(editingDailyTaskId.value, dailyTaskForm);
      ElMessage.success("每日子任务已更新");
    } else {
      await createPersonalTask(dailyTaskForm);
      ElMessage.success("每日子任务已新增");
    }
    dailyTaskDialogVisible.value = false;
    await refreshData();
  } finally {
    dailySubmitting.value = false;
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
    ElMessage.success("任务已完成，并已记录完成情况");
    await refreshData();
  } finally {
    completeSubmitting.value = false;
  }
}

async function handleDeleteTask(taskId: number, label: string) {
  try {
    await ElMessageBox.confirm(
      `确认删除这条${label}吗？删除后不会进入个人历史，且无法恢复。`,
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
  ElMessage.success(`${label}已删除`);
  await refreshData();
}

onMounted(async () => {
  await refreshData();
});

watch(filteredLongTasks, (items) => {
  if (!items.length) {
    selectedTask.value = null;
    subtasks.value = [];
    completedSubtasks.value = [];
    return;
  }

  if (!selectedTask.value || !items.some((item) => item.id === selectedTask.value?.id)) {
    selectedTask.value = items[0];
    void loadSubtasks();
  }
});

watch(longTaskDialogVisible, (visible) => {
  if (!visible) {
    resetLongTaskForm();
    longTaskSnapshot.value = "";
  }
});

watch(dailyTaskDialogVisible, (visible) => {
  if (!visible) {
    resetDailyTaskForm();
    dailyTaskSnapshot.value = "";
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

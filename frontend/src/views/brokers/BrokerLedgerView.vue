<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">券商列表</p>
        <h2>统一维护券商状态、版本、服务器和委托主站基础信息。</h2>
        <p>这里是券商管理的总入口。点击系统版本、服务器数量、委托主站数量和当前项目数，会分别跳转到对应管理页面。</p>
      </div>
      <div class="hero-actions">
        <el-button @click="downloadBrokerCsv">导出 CSV</el-button>
        <el-button type="primary" @click="openCreateBrokerDialog">新增券商</el-button>
      </div>
    </section>

    <section class="section-card">
      <section class="compact-grid compact-grid-4" style="margin-bottom: 16px;">
        <article class="compact-card">
          <small>券商总数</small>
          <strong>{{ brokerStats.total }}</strong>
        </article>
        <article class="compact-card">
          <small>已上线 / 待上线</small>
          <strong>{{ brokerStats.online }}/{{ brokerStats.pendingOnline }}</strong>
        </article>
        <article class="compact-card">
          <small>对接中 / 待对接</small>
          <strong>{{ brokerStats.integrating }}/{{ brokerStats.pendingIntegration }}</strong>
        </article>
        <article class="compact-card">
          <small>待下线</small>
          <strong>{{ brokerStats.pendingOffline }}</strong>
        </article>
      </section>

      <div class="section-title">
        <div>
          <h3>券商列表</h3>
          <p>当前共 {{ brokers.length }} 家券商。</p>
        </div>
      </div>

      <el-table v-if="brokers.length" :data="brokers" stripe>
        <el-table-column prop="name" label="券商名称" min-width="180" />
        <el-table-column label="券商状态" min-width="110">
          <template #default="{ row }">
            <StatusTag :label="row.businessStatus" />
          </template>
        </el-table-column>
        <el-table-column label="系统版本" min-width="150">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/brokers/versions?brokerId=${row.id}`)">
              {{ row.systemVersion || "-" }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="服务器数量" min-width="110">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/brokers/servers?brokerId=${row.id}`)">
              {{ row.serverCount }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="委托主站数量" min-width="130">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/brokers/entrust-sites?brokerId=${row.id}`)">
              {{ row.entrustSiteCount }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="当前项目数" min-width="110">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/projects?broker_id=${row.id}`)">
              {{ row.currentProjects }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="nextMilestone" label="最近关键节点" min-width="180" />
        <el-table-column label="操作" min-width="140" fixed="right">
          <template #default="{ row }">
            <div class="action-row">
              <el-button link type="primary" @click="openEditBrokerDialog(row)">编辑</el-button>
              <el-button link type="danger" @click="handleDeleteBroker(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <EmptyBlock
        v-else
        title="还没有券商管理数据"
        description="先新增一条券商记录，后续版本、服务器、委托主站和项目关系都从这里展开。"
      >
        <div class="empty-inline-action">
          <el-button type="primary" @click="openCreateBrokerDialog">新增券商</el-button>
        </div>
      </EmptyBlock>
    </section>

    <el-dialog v-model="brokerDialogVisible" :title="editingBrokerId ? '编辑券商' : '新增券商'" width="760px">
      <el-form ref="brokerFormRef" :model="brokerForm" :rules="brokerRules" label-width="120px">
        <el-form-item label="券商名称" prop="name">
          <el-input v-model="brokerForm.name" />
        </el-form-item>
        <el-form-item label="券商简称" prop="short_name">
          <el-input v-model="brokerForm.short_name" />
        </el-form-item>
        <el-form-item label="对接人">
          <el-input v-model="brokerForm.contact_name" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="brokerForm.contact_phone" />
        </el-form-item>
        <el-form-item label="启停状态" prop="status">
          <el-select v-model="brokerForm.status" style="width: 100%;">
            <el-option label="启用" value="active" />
            <el-option label="停用" value="inactive" />
          </el-select>
        </el-form-item>
        <el-form-item label="券商状态" prop="business_status">
          <el-select v-model="brokerForm.business_status" style="width: 100%;">
            <el-option label="已上线" value="已上线" />
            <el-option label="待上线" value="待上线" />
            <el-option label="对接中" value="对接中" />
            <el-option label="待对接" value="待对接" />
            <el-option label="待下线" value="待下线" />
          </el-select>
        </el-form-item>
        <el-form-item label="系统版本">
          <el-input v-model="brokerForm.system_version" placeholder="例如 V6.3.12" />
        </el-form-item>
        <el-form-item label="版本更新时间">
          <el-date-picker v-model="brokerForm.system_version_updated_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="版本内容">
          <el-input v-model="brokerForm.system_version_content" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="brokerForm.note" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="brokerDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSaveBroker">保存券商</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from "element-plus";
import { useRouter } from "vue-router";

import { createBroker, deleteBroker, getBrokerDetail, getBrokers, updateBroker } from "../../api/brokers";
import EmptyBlock from "../../components/EmptyBlock.vue";
import StatusTag from "../../components/StatusTag.vue";
import type { BrokerCreatePayload, BrokerDetail, BrokerSummary } from "../../types/models";

const router = useRouter();
const brokers = ref<BrokerSummary[]>([]);
const brokerDialogVisible = ref(false);
const submitting = ref(false);
const editingBrokerId = ref<number | null>(null);
const brokerFormRef = ref<FormInstance>();

const brokerForm = reactive<BrokerCreatePayload>({
  name: "",
  short_name: "",
  contact_name: "",
  contact_phone: "",
  status: "active",
  business_status: "待对接",
  system_version: "",
  system_version_updated_at: "",
  system_version_content: "",
  note: ""
});

const brokerRules: FormRules<BrokerCreatePayload> = {
  name: [{ required: true, message: "请输入券商名称", trigger: "blur" }],
  short_name: [{ required: true, message: "请输入券商简称", trigger: "blur" }],
  status: [{ required: true, message: "请选择启停状态", trigger: "change" }],
  business_status: [{ required: true, message: "请选择券商状态", trigger: "change" }]
};

const brokerStats = computed(() => ({
  total: brokers.value.length,
  online: brokers.value.filter((item) => item.businessStatus === "已上线").length,
  pendingOnline: brokers.value.filter((item) => item.businessStatus === "待上线").length,
  integrating: brokers.value.filter((item) => item.businessStatus === "对接中").length,
  pendingIntegration: brokers.value.filter((item) => item.businessStatus === "待对接").length,
  pendingOffline: brokers.value.filter((item) => item.businessStatus === "待下线").length
}));

async function loadBrokers() {
  brokers.value = await getBrokers();
}

function resetBrokerForm() {
  editingBrokerId.value = null;
  brokerForm.name = "";
  brokerForm.short_name = "";
  brokerForm.contact_name = "";
  brokerForm.contact_phone = "";
  brokerForm.status = "active";
  brokerForm.business_status = "待对接";
  brokerForm.system_version = "";
  brokerForm.system_version_updated_at = "";
  brokerForm.system_version_content = "";
  brokerForm.note = "";
}

function fillBrokerForm(detail: BrokerDetail) {
  brokerForm.name = detail.name;
  brokerForm.short_name = detail.shortName;
  brokerForm.contact_name = detail.contactName;
  brokerForm.contact_phone = detail.contactPhone;
  brokerForm.status = detail.status;
  brokerForm.business_status = detail.businessStatus;
  brokerForm.system_version = detail.systemVersion;
  brokerForm.system_version_updated_at = detail.systemVersionUpdatedAt ? detail.systemVersionUpdatedAt.replace(" ", "T") : "";
  brokerForm.system_version_content = detail.systemVersionContent;
  brokerForm.note = detail.note;
}

function openCreateBrokerDialog() {
  resetBrokerForm();
  brokerDialogVisible.value = true;
}

async function openEditBrokerDialog(broker: BrokerSummary) {
  const detail = await getBrokerDetail(broker.id);
  editingBrokerId.value = broker.id;
  fillBrokerForm(detail);
  brokerDialogVisible.value = true;
}

async function handleSaveBroker() {
  const valid = await brokerFormRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }
  submitting.value = true;
  try {
    if (editingBrokerId.value) {
      await updateBroker(editingBrokerId.value, brokerForm);
      ElMessage.success("券商已更新");
    } else {
      await createBroker(brokerForm);
      ElMessage.success("券商已新增");
    }
    brokerDialogVisible.value = false;
    await loadBrokers();
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || "保存券商失败");
  } finally {
    submitting.value = false;
  }
}

async function handleDeleteBroker(broker: BrokerSummary) {
  await ElMessageBox.confirm(`确认删除券商“${broker.name}”吗？如果该券商下已有项目，会一并删除。`, "删除确认", {
    type: "warning",
    confirmButtonText: "确认删除",
    cancelButtonText: "取消"
  });
  await deleteBroker(broker.id);
  ElMessage.success("券商已删除");
  await loadBrokers();
}

function downloadBrokerCsv() {
  const header = ["券商名称", "券商状态", "系统版本", "服务器数量", "委托主站数量", "当前项目数"];
  const rows = brokers.value.map((item) => [
    item.name,
    item.businessStatus,
    item.systemVersion,
    item.serverCount,
    item.entrustSiteCount,
    item.currentProjects
  ]);
  const csv = [header, ...rows]
    .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(","))
    .join("\n");

  const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "券商列表.csv";
  link.click();
  URL.revokeObjectURL(url);
  ElMessage.success("券商列表 CSV 已导出");
}

onMounted(async () => {
  await loadBrokers();
});
</script>

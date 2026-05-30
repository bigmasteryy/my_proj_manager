<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">版本管理</p>
        <h2>查看并维护各家券商的系统版本与版本内容。</h2>
        <p>点击券商列表里的系统版本会直接跳到这里，并自动定位到对应券商。</p>
      </div>
      <div class="hero-actions">
        <el-select v-model="selectedBrokerId" style="width: 260px;" filterable placeholder="选择券商" @change="handleBrokerChange">
          <el-option v-for="broker in brokers" :key="broker.id" :label="broker.name" :value="broker.id" />
        </el-select>
      </div>
    </section>

    <section class="section-card" v-loading="loading">
      <template v-if="detail">
        <div class="section-title">
          <div>
            <h3>{{ detail.name }}</h3>
            <p>券商状态：{{ detail.businessStatus }}</p>
          </div>
          <el-button type="primary" @click="openVersionDialog">编辑版本</el-button>
        </div>

        <div class="note-panel">
          <small>当前版本</small>
          <strong>{{ detail.systemVersion || "-" }}</strong>
          <small>更新时间</small>
          <strong>{{ detail.systemVersionUpdatedAt || "-" }}</strong>
          <small>版本内容</small>
          <div class="table-multiline">{{ detail.systemVersionContent || "-" }}</div>
        </div>
      </template>
      <EmptyBlock
        v-else-if="!loading"
        compact
        title="请选择一家具商"
        description="选择券商后就能在这里维护系统版本和版本内容。"
      />
    </section>

    <el-dialog v-model="versionDialogVisible" title="编辑系统版本" width="680px">
      <el-form :model="versionForm" label-width="120px">
        <el-form-item label="系统版本">
          <el-input v-model="versionForm.system_version" />
        </el-form-item>
        <el-form-item label="更新时间">
          <el-date-picker v-model="versionForm.system_version_updated_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="版本内容">
          <el-input v-model="versionForm.system_version_content" type="textarea" :rows="6" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="versionDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSaveVersion">保存版本</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import { getBrokerDetail, getBrokers, updateBroker } from "../../api/brokers";
import EmptyBlock from "../../components/EmptyBlock.vue";
import type { BrokerCreatePayload, BrokerDetail, BrokerSummary } from "../../types/models";

const route = useRoute();
const router = useRouter();

const brokers = ref<BrokerSummary[]>([]);
const detail = ref<BrokerDetail | null>(null);
const selectedBrokerId = ref<number | null>(null);
const loading = ref(false);
const submitting = ref(false);
const versionDialogVisible = ref(false);

const versionForm = reactive<Pick<BrokerCreatePayload, "system_version" | "system_version_updated_at" | "system_version_content">>({
  system_version: "",
  system_version_updated_at: "",
  system_version_content: ""
});

async function loadBrokers() {
  brokers.value = await getBrokers();
}

async function loadDetail(brokerId: number) {
  loading.value = true;
  try {
    detail.value = await getBrokerDetail(brokerId);
  } finally {
    loading.value = false;
  }
}

function openVersionDialog() {
  versionForm.system_version = detail.value?.systemVersion || "";
  versionForm.system_version_updated_at = detail.value?.systemVersionUpdatedAt ? detail.value.systemVersionUpdatedAt.replace(" ", "T") : "";
  versionForm.system_version_content = detail.value?.systemVersionContent || "";
  versionDialogVisible.value = true;
}

async function handleSaveVersion() {
  if (!detail.value) {
    return;
  }
  submitting.value = true;
  try {
    await updateBroker(detail.value.id, {
      name: detail.value.name,
      short_name: detail.value.shortName,
      contact_name: detail.value.contactName,
      contact_phone: detail.value.contactPhone,
      status: detail.value.status,
      business_status: detail.value.businessStatus,
      system_version: versionForm.system_version,
      system_version_updated_at: versionForm.system_version_updated_at,
      system_version_content: versionForm.system_version_content,
      note: detail.value.note
    });
    versionDialogVisible.value = false;
    await loadDetail(detail.value.id);
    ElMessage.success("系统版本已更新");
  } finally {
    submitting.value = false;
  }
}

async function handleBrokerChange(brokerId: number) {
  await router.replace(`/brokers/versions?brokerId=${brokerId}`);
}

onMounted(async () => {
  await loadBrokers();
  const queryBrokerId = Number(route.query.brokerId || 0);
  selectedBrokerId.value = queryBrokerId || brokers.value[0]?.id || null;
  if (selectedBrokerId.value) {
    await loadDetail(selectedBrokerId.value);
  }
});

watch(
  () => route.query.brokerId,
  async (value) => {
    const brokerId = Number(value || 0);
    if (!brokerId) {
      return;
    }
    selectedBrokerId.value = brokerId;
    await loadDetail(brokerId);
  }
);
</script>

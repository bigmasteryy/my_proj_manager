<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">用户管理</p>
        <h2>维护系统登录用户和角色权限。</h2>
        <p>当前先提供内部最小闭环：新增用户、编辑资料、重置密码。</p>
      </div>
      <div class="hero-actions">
        <el-button type="primary" @click="openCreateDialog">新增用户</el-button>
      </div>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>用户列表</h3>
          <p>当前共有 {{ users.length }} 位用户。</p>
        </div>
      </div>
      <el-table v-if="users.length" :data="users" stripe>
        <el-table-column prop="username" label="用户名" min-width="140" />
        <el-table-column prop="displayName" label="姓名" min-width="140" />
        <el-table-column label="角色" min-width="100">
          <template #default="{ row }">
            {{ row.role === 'admin' ? '管理员' : '普通用户' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="100">
          <template #default="{ row }">
            <StatusTag :label="row.status === 'active' ? '启用' : '停用'" />
          </template>
        </el-table-column>
        <el-table-column prop="lastLoginAt" label="最近登录" min-width="160" />
        <el-table-column prop="createdAt" label="创建时间" min-width="160" />
        <el-table-column label="操作" min-width="200" fixed="right">
          <template #default="{ row }">
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
              <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
              <el-button link type="warning" @click="openResetPasswordDialog(row)">重置密码</el-button>
              <el-button link type="danger" @click="handleDeleteUser(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <EmptyBlock
        v-else
        title="还没有用户"
        description="先新增一个系统用户，后续即可通过账号密码登录。"
      >
        <div class="empty-inline-action">
          <el-button type="primary" @click="openCreateDialog">新增用户</el-button>
        </div>
      </EmptyBlock>
    </section>

    <el-dialog v-model="userDialogVisible" :title="editingUserId ? '编辑用户' : '新增用户'" width="620px">
      <el-form ref="userFormRef" :model="userForm" :rules="userRules" label-width="110px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" :disabled="Boolean(editingUserId)" />
        </el-form-item>
        <el-form-item label="姓名" prop="display_name">
          <el-input v-model="userForm.display_name" />
        </el-form-item>
        <el-form-item v-if="!editingUserId" label="初始密码" prop="password">
          <el-input v-model="userForm.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" style="width: 100%;">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="userForm.status" style="width: 100%;">
            <el-option label="启用" value="active" />
            <el-option label="停用" value="inactive" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSaveUser">保存用户</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="passwordDialogVisible" title="重置密码" width="560px">
      <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="110px">
        <el-form-item label="用户" prop="display_name">
          <el-input :model-value="resettingUserName" disabled />
        </el-form-item>
        <el-form-item label="新密码" prop="password">
          <el-input v-model="passwordForm.password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="passwordSubmitting" @click="handleResetPassword">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from "element-plus";
import { createUser, deleteUser, getUsers, resetUserPassword, updateUser } from "../../api/users";
import EmptyBlock from "../../components/EmptyBlock.vue";
import StatusTag from "../../components/StatusTag.vue";
import type { AuthUser, UserCreatePayload, UserResetPasswordPayload, UserUpdatePayload } from "../../types/models";

const users = ref<AuthUser[]>([]);
const userDialogVisible = ref(false);
const passwordDialogVisible = ref(false);
const submitting = ref(false);
const passwordSubmitting = ref(false);
const editingUserId = ref<number | null>(null);
const resettingUserId = ref<number | null>(null);
const resettingUserName = ref("");
const userFormRef = ref<FormInstance>();
const passwordFormRef = ref<FormInstance>();

const userForm = reactive<UserCreatePayload>({
  username: "",
  display_name: "",
  password: "",
  role: "user",
  status: "active"
});

const passwordForm = reactive<UserResetPasswordPayload>({
  password: ""
});

const userRules: FormRules<UserCreatePayload> = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  display_name: [{ required: true, message: "请输入姓名", trigger: "blur" }],
  password: [{ required: true, message: "请输入初始密码", trigger: "blur" }],
  role: [{ required: true, message: "请选择角色", trigger: "change" }],
  status: [{ required: true, message: "请选择状态", trigger: "change" }]
};

const passwordRules: FormRules<UserResetPasswordPayload> = {
  password: [{ required: true, message: "请输入新密码", trigger: "blur" }]
};

async function loadUsers() {
  users.value = await getUsers();
}

function resetUserForm() {
  editingUserId.value = null;
  userForm.username = "";
  userForm.display_name = "";
  userForm.password = "";
  userForm.role = "user";
  userForm.status = "active";
}

function openCreateDialog() {
  resetUserForm();
  userDialogVisible.value = true;
}

function openEditDialog(user: AuthUser) {
  editingUserId.value = user.id;
  userForm.username = user.username;
  userForm.display_name = user.displayName;
  userForm.password = "";
  userForm.role = user.role;
  userForm.status = user.status;
  userDialogVisible.value = true;
}

function openResetPasswordDialog(user: AuthUser) {
  resettingUserId.value = user.id;
  resettingUserName.value = `${user.displayName}（${user.username}）`;
  passwordForm.password = "";
  passwordDialogVisible.value = true;
}

async function handleSaveUser() {
  const valid = await userFormRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  submitting.value = true;
  try {
    if (editingUserId.value) {
      const payload: UserUpdatePayload = {
        display_name: userForm.display_name,
        role: userForm.role,
        status: userForm.status
      };
      await updateUser(editingUserId.value, payload);
      ElMessage.success("用户已更新");
    } else {
      await createUser(userForm);
      ElMessage.success("用户已新增");
    }
    userDialogVisible.value = false;
    await loadUsers();
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || "保存用户失败");
  } finally {
    submitting.value = false;
  }
}

async function handleResetPassword() {
  const valid = await passwordFormRef.value?.validate().catch(() => false);
  if (!valid || !resettingUserId.value) {
    return;
  }

  passwordSubmitting.value = true;
  try {
    await resetUserPassword(resettingUserId.value, passwordForm);
    passwordDialogVisible.value = false;
    ElMessage.success("密码已重置");
  } finally {
    passwordSubmitting.value = false;
  }
}

async function handleDeleteUser(user: AuthUser) {
  await ElMessageBox.confirm(`确认删除用户“${user.displayName}（${user.username}）”？`, "删除确认", {
    type: "warning",
    confirmButtonText: "确认删除",
    cancelButtonText: "取消"
  });

  try {
    await deleteUser(user.id);
    ElMessage.success("用户已删除");
    await loadUsers();
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || "删除用户失败");
  }
}

onMounted(async () => {
  await loadUsers();
});
</script>

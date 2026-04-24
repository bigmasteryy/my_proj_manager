<template>
  <div class="login-shell">
    <section class="login-card">
      <div>
        <p class="eyebrow">登录</p>
        <h1>项目管理平台</h1>
        <p class="compact-muted">请输入账号密码进入系统。</p>
      </div>

      <el-alert
        title="默认管理员：admin / admin123"
        type="info"
        :closable="false"
        style="margin-bottom: 18px;"
      />

      <el-alert
        v-if="loginError"
        :title="loginError"
        type="error"
        :closable="false"
        style="margin-bottom: 18px;"
      />

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" @input="clearError" @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" @input="clearError" @keyup.enter="handleLogin" />
        </el-form-item>
      </el-form>

      <div class="hero-actions" style="justify-content: flex-end;">
        <el-button type="primary" :loading="submitting" @click="handleLogin">登录</el-button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import { useRoute, useRouter } from "vue-router";
import { getCurrentUserProfile, login } from "../../api/auth";
import type { LoginPayload } from "../../types/models";
import { saveSession } from "../../utils/auth";

const router = useRouter();
const route = useRoute();
const formRef = ref<FormInstance>();
const submitting = ref(false);
const loginError = ref("");
const form = reactive<LoginPayload>({
  username: "admin",
  password: "admin123"
});

const rules: FormRules<LoginPayload> = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }]
};

function clearError() {
  loginError.value = "";
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  loginError.value = "";
  submitting.value = true;
  try {
    const result = await login(form);
    saveSession(result.token, result.user);
    const current = await getCurrentUserProfile();
    saveSession(result.token, current);
    ElMessage.success("登录成功");
    const redirect = typeof route.query.redirect === "string"
      ? route.query.redirect
      : current.role === "admin"
        ? "/dashboard"
        : "/personal";
    router.replace(redirect);
  } catch (error: any) {
    if (!error?.response) {
      loginError.value = "登录服务暂不可用，请确认后端服务已经启动。";
    } else if (error.response.status === 403) {
      loginError.value = error?.response?.data?.detail || "账号已停用，请联系管理员。";
    } else if (error.response.status === 401) {
      loginError.value = "用户名或密码错误，请重新输入。";
    } else {
      loginError.value = error?.response?.data?.detail || "登录失败，请稍后再试。";
    }
    ElMessage.error(loginError.value);
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.login-shell {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.login-card {
  width: min(460px, 100%);
  padding: 28px;
  border: 1px solid var(--border);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: var(--shadow);
}

.login-card h1 {
  margin: 0;
  font-size: 32px;
  line-height: 1.1;
}
</style>

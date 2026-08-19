<script setup lang="ts">
import { Calendar, DataLine, EditPen, MagicStick } from "@element-plus/icons-vue";

import PageHeader from "../components/PageHeader.vue";

const summaryCards = [
  { title: "首页视觉", value: "01", description: "当前已接入欢迎页配置和名句轮播", icon: MagicStick },
  { title: "文章模块", value: "04", description: "已预留列表、编辑、标签、分类扩展位", icon: EditPen },
  { title: "内容计划", value: "03", description: "媒体、关于自己、系统设置待继续落地", icon: DataLine },
  { title: "上线节奏", value: "本周", description: "建议优先补文章管理和图片上传", icon: Calendar },
];

const todoList = [
  "接入文章列表与文章编辑页",
  "把首页封面图 URL 升级成图片上传",
  "补齐关于自己模块的数据表单",
  "增加系统设置与操作日志入口",
];
</script>

<template>
  <div class="page-stack">
    <PageHeader
      eyebrow="DASHBOARD"
      title="控制台"
      description="这是后台的总览工作台，用来快速查看当前模块准备情况和下一步开发重点。"
    />

    <el-row :gutter="16">
      <el-col v-for="card in summaryCards" :key="card.title" :xs="24" :sm="12" :xl="6">
        <el-card shadow="hover" class="dashboard-stat-card">
          <div class="dashboard-stat-top">
            <div>
              <p class="dashboard-stat-title">{{ card.title }}</p>
              <strong>{{ card.value }}</strong>
            </div>
            <el-icon class="dashboard-stat-icon"><component :is="card.icon" /></el-icon>
          </div>
          <p class="dashboard-stat-text">{{ card.description }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="16">
        <el-card shadow="never" class="dashboard-panel">
          <template #header>
            <div class="panel-header">
              <span>当前后台模块</span>
              <el-tag type="warning">企业级结构已就绪</el-tag>
            </div>
          </template>
          <div class="dashboard-module-grid">
            <div class="dashboard-module-item">
              <h3>控制台</h3>
              <p>模块总览、开发节奏与后续重点入口。</p>
            </div>
            <div class="dashboard-module-item">
              <h3>站点设置</h3>
              <p>首页欢迎页、封面图、品牌名与名句轮播配置。</p>
            </div>
            <div class="dashboard-module-item">
              <h3>文章管理</h3>
              <p>预留文章列表、编辑器、发布流程和分类标签。</p>
            </div>
            <div class="dashboard-module-item">
              <h3>媒体资源</h3>
              <p>预留图片上传、资源列表和引用管理能力。</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="8">
        <el-card shadow="never" class="dashboard-panel">
          <template #header>
            <div class="panel-header">
              <span>下一步建议</span>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="item in todoList"
              :key="item"
              type="warning"
              hollow
              :timestamp="'推荐优先级'"
            >
              {{ item }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

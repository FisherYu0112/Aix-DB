***REMOVED***
    <n-layout>
        <n-layout-header class="header">
  ***REMOVED***class="header-content">
                <!-- 这里可以放置一些顶部的内容或导航 -->
***REMOVED***
            <button class="create-project-btn" @click="createProject">
                + 创建项目
  ***REMOVED***
        </n-layout-header>
        <n-layout-content>
  ***REMOVED***class="container">
      ***REMOVED***class="card" v-for="(item, index***REMOVED*** in items" :key="index">
          ***REMOVED***class="card-header">
                        <img :src="item.icon" alt="" class="card-icon" />
                        <span class="card-title">{{ item.title ***REMOVED******REMOVED***</span>
        ***REMOVED***
          ***REMOVED***class="card-body">
                        <p>{{ item.description ***REMOVED******REMOVED***</p>
        ***REMOVED***
          ***REMOVED***class="card-footer">
                        <span class="card-info"
                  ***REMOVED***用户需求: {{ item.userDemand ***REMOVED******REMOVED***</span
              ***REMOVED***
                        <span class="card-date">{{ item.date ***REMOVED******REMOVED***</span>
                        <button class="card-button" @click="showMore(item***REMOVED***">
                            ...
              ***REMOVED***
        ***REMOVED***
    ***REMOVED***
***REMOVED***
        </n-layout-content>
  ***REMOVED***
***REMOVED***

<script setup>
import { ref ***REMOVED*** from 'vue'
import { NLayout, NLayoutHeader, NLayoutContent ***REMOVED*** from 'naive-ui'

const items = ref([
  ***REMOVED***
        icon: 'https://example.com/icon.png',
        title: '需求1',
        description: '这是第一个需求的描述。',
        userDemand: '5',
        date: '2025-01-21 10:17'
    ***REMOVED***,
  ***REMOVED***
        icon: 'https://example.com/icon2.png',
        title: '需求2',
        description: '这是第二个需求的描述。',
        userDemand: '7',
        date: '2025-01-21 10:25'
    ***REMOVED***
    // 继续添加更多项目...
]***REMOVED***

const showMore = (item***REMOVED*** => {
    console.log(`Showing more details for ${item.title***REMOVED***`***REMOVED***
***REMOVED***

const createProject = (***REMOVED*** => {
    console.log('Creating a new project'***REMOVED***
***REMOVED***
***REMOVED***

***REMOVED***
.header {
  ***REMOVED***
    justify-content: space-between;
    align-items: center;
  ***REMOVED*** /* 调整padding以适应设计 */
    background-color: #f8f8f8; /* 根据需要调整背景颜色 */
***REMOVED***

.header-content {
    /* 这里可以添加任何必要的样式，比如logo或导航链接 */
***REMOVED***

.create-project-btn {
    background-color: #2c7be5;
    color: #fff;
  ***REMOVED***
  ***REMOVED***
    border-radius: 20px;
  ***REMOVED***
    font-size: 14px;
***REMOVED***

.container {
  ***REMOVED***
    flex-wrap: wrap;
    gap: 20px;
  ***REMOVED***
***REMOVED***

.card {
    width: 250px;
    margin-top: 40px;
  ***REMOVED***
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1***REMOVED***;
    background-color: #ffffff;
    overflow: hidden;
***REMOVED***

.card-header {
  ***REMOVED***
    align-items: center;
  ***REMOVED***
    background-color: #f9f9f9;
***REMOVED***

.card-icon {
    width: 20px;
    height: 20px;
  ***REMOVED***
***REMOVED***

.card-title {
    font-weight: bold;
***REMOVED***

.card-body {
  ***REMOVED***
***REMOVED***

.card-footer {
  ***REMOVED***
    justify-content: space-between;
  ***REMOVED***
  ***REMOVED***
***REMOVED***

.card-info,
.card-date {
    font-size: 12px;
  ***REMOVED***
***REMOVED***

.card-button {
    background-color: #e0e0e0;
  ***REMOVED***
    padding: 5px 10px;
  ***REMOVED***
  ***REMOVED***
    font-size: 12px;
***REMOVED***
***REMOVED***

<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
const items = ref([])
const onlyValid = ref(true)
const lookupId = ref(null)
const detail = ref(null)
const error = ref('')
const load = async () => {
  error.value = ''
  items.value = (await getJSON(`/api/history?only_valid=${onlyValid.value}`)).items
}
const invalidate = async (id) => {
  error.value = ''
  try {
    await postJSON(`/api/history/${id}/invalidate`, {})
    if (detail.value?.id === id) detail.value = await getJSON(`/api/history/${id}`)
    await load()
  } catch (e) { error.value = `作废 #${id} 失败：${e.message}` }
}
const lookup = async () => {
  error.value = ''; detail.value = null
  if (!lookupId.value) return
  try { detail.value = await getJSON(`/api/history/${lookupId.value}`) }
  catch (e) { error.value = `查看 #${lookupId.value} 失败：${e.message}` }
}
const num = (v) => (v === undefined || v === null ? '—' : v)
onMounted(load)
</script>
<template><div class="page"><h1>试算记录</h1>
<p>
  <label><input type="checkbox" v-model="onlyValid" @change="load" /> 只看有效</label>
  <input v-model.number="lookupId" type="number" placeholder="编号" />
  <button @click="lookup">按编号查看</button>
</p>
<p v-if="error" class="error">{{ error }}</p>
<div v-if="detail" class="run-detail">
  <h2>#{{ detail.id }}<span v-if="detail.status !== 'valid'">（已失效，只读）</span></h2>
  <p>月供 {{ num(detail.result.monthly_payment) }} · 利息合计 {{ num(detail.result.total_interest) }}</p>
  <p>创建 {{ detail.created_at }}<template v-if="detail.invalidated_at"> · 失效于 {{ detail.invalidated_at }}</template><template v-if="detail.supersedes_id"> · 前序 #{{ detail.supersedes_id }}</template></p>
</div>
<table>
  <tr><th>#</th><th>时间</th><th>类型</th><th>月供</th><th>利息合计</th><th>状态</th><th>前序</th><th></th></tr>
  <tr v-for="h in items" :key="h.id">
    <td>#{{ h.id }}</td><td>{{ h.created_at }}</td><td>{{ h.kind }}</td>
    <td>{{ num(h.result.monthly_payment) }}</td><td>{{ num(h.result.total_interest) }}</td>
    <td>{{ h.status === 'valid' ? '有效' : '已失效' }}</td>
    <td>{{ h.supersedes_id ? `#${h.supersedes_id}` : '' }}</td>
    <td><button v-if="h.status === 'valid'" @click="invalidate(h.id)">作废</button></td>
  </tr>
</table>
</div></template>

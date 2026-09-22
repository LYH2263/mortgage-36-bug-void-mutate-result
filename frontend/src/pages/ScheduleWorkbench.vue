<script setup>
import { ref } from 'vue'
import { postJSON } from '../api'
const principal = ref(800000)
const annual_rate = ref(4.2)
const months = ref(360)
const out = ref(null)
const runId = ref(null)
const msg = ref('')
const err = ref('')
const calc = () => postJSON('/api/schedule', { principal: principal.value, annual_rate: annual_rate.value, months: months.value, persist: true })
const run = async () => {
  err.value = ''; msg.value = ''
  out.value = await calc()
  runId.value = out.value.run_id
  msg.value = `已保存新记录 #${runId.value}`
}
const retest = async () => {
  err.value = ''; msg.value = ''
  const prev = runId.value
  try {
    await postJSON(`/api/history/${prev}/invalidate`, {})
    out.value = await postJSON('/api/schedule', { principal: principal.value, annual_rate: annual_rate.value, months: months.value, persist: true, supersedes_id: prev })
    runId.value = out.value.run_id
    msg.value = `已作废 #${prev}，重测保存为 #${runId.value}`
  } catch (e) { err.value = `重测失败：${e.message}` }
}
</script>
<template><div class="page"><h1>等额本息试算</h1>
<label>本金 <input v-model.number="principal" /></label>
<label>年利率% <input v-model.number="annual_rate" /></label>
<label>月数 <input v-model.number="months" /></label>
<button @click="run">计算</button>
<button v-if="runId" @click="retest">重测（作废 #{{ runId }} 并重算）</button>
<p v-if="out">月供 {{ out.monthly_payment }} · 利息合计 {{ out.total_interest }}</p>
<p v-if="msg">{{ msg }}</p>
<p v-if="err" class="error">{{ err }}</p>
</div></template>

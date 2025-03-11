<script setup>
const props = defineProps({
  selectedFilters: {
    type: Array,
    required: true
  }
})

const categories = ['ozone', 'emissions', 'compliance', 'policy']

const emit = defineEmits(['update:selectedFilters'])

const toggleFilter = (category) => {
  const newFilters = props.selectedFilters.includes(category)
    ? props.selectedFilters.filter(f => f !== category)
    : [...props.selectedFilters, category]
  emit('update:selectedFilters', newFilters)
}
</script>

<template>
  <div class="sidebar">
    <h3>Filter Results</h3>
    <div class="filter-options">
      <label v-for="category in categories" :key="category">
        <input 
          type="checkbox" 
          :value="category"
          :checked="selectedFilters.includes(category)"
          @change="toggleFilter(category)"
          class="filter-checkbox"
        > {{ category }}
      </label>
    </div>
  </div>
</template> 
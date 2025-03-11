<script setup>
const props = defineProps({
  selectedFilters: {
    type: Object,
    required: true
  },
  availableFilters: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:selectedFilters'])

const toggleFilter = (filterType, value) => {
  const currentFilters = props.selectedFilters[filterType]
  const newFilters = currentFilters.includes(value)
    ? currentFilters.filter(f => f !== value)
    : [...currentFilters, value]
  
  emit('update:selectedFilters', {
    ...props.selectedFilters,
    [filterType]: newFilters
  })
}

// Filter category labels
const filterLabels = {
  documentType: 'Document Type',
  jurisdiction: 'Jurisdiction'
}
</script>

<template>
  <div class="sidebar">
    <h3>Filter Results</h3>
    <div v-if="Object.values(availableFilters).every(filters => filters.length === 0)" class="no-filters">
      Search for documents to see available filters
    </div>
    <div v-else class="filter-categories">
      <div 
        v-for="(values, filterType) in availableFilters" 
        :key="filterType"
        class="filter-category"
        v-show="values.length > 0"
      >
        <h4>{{ filterLabels[filterType] }}</h4>
        <div class="filter-options">
          <label v-for="value in values" :key="value">
            <input 
              type="checkbox" 
              :value="value"
              :checked="selectedFilters[filterType].includes(value)"
              @change="toggleFilter(filterType, value)"
              class="filter-checkbox"
            > {{ value }}
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.no-filters {
  color: #8B8C89;
  font-style: italic;
  font-size: 0.9em;
  margin-top: 1rem;
}

.filter-categories {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.filter-category h4 {
  font-family: 'Roboto Condensed', sans-serif;
  color: #274C77;
  margin: 0 0 0.5rem 0;
  font-size: 1em;
}

.filter-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-checkbox {
  margin-right: 0.5rem;
}
</style> 
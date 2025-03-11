<script setup>
import Filters from './Filters.vue'

const props = defineProps({
  documents: {
    type: Array,
    required: true
  },
  savedDocuments: {
    type: Array,
    required: true
  },
  filteredDocuments: {
    type: Array,
    required: true
  },
  paginatedResults: {
    type: Array,
    required: true
  },
  currentPage: {
    type: Number,
    required: true
  },
  totalPages: {
    type: Number,
    required: true
  },
  searchQuery: {
    type: String,
    required: true
  },
  selectedFilters: {
    type: Array,
    required: true
  }
})

const emit = defineEmits([
  'update:searchQuery',
  'update:selectedFilters',
  'update:currentPage',
  'toggleFolder',
  'enterChat'
])
</script>

<template>
  <div id="searchMode">
    <!-- Sidebar with Filter Checkboxes -->
    <Filters
      :selectedFilters="selectedFilters"
      @update:selectedFilters="emit('update:selectedFilters', $event)"
    />

    <!-- Main Search and Results Area -->
    <div class="main">
      <div class="search-bar">
        <input 
          type="text" 
          :value="searchQuery"
          @input="emit('update:searchQuery', $event.target.value)"
          placeholder="What can I help you find?"
        >
        <button @click="emit('update:currentPage', 1)">Search</button>
      </div>

      <div class="results">
        <p class="result-count">{{ filteredDocuments.length }} document(s) found</p>
        <div class="search-results">
          <div 
            v-for="item in paginatedResults" 
            :key="item.title"
            class="result-item"
          >
            <div>
              <h3>{{ item.title }}</h3>
              <p>{{ item.description }}</p>
            </div>
            <button 
              class="add-to-folder"
              :class="{ added: savedDocuments.includes(item.title) }"
              @click="emit('toggleFolder', item.title)"
            >+</button>
          </div>
        </div>

        <div class="pagination">
          <button 
            :disabled="currentPage <= 1"
            @click="emit('update:currentPage', currentPage - 1)"
          >Previous</button>
          <button 
            :disabled="currentPage >= totalPages"
            @click="emit('update:currentPage', currentPage + 1)"
          >Next</button>
        </div>
      </div>
    </div>

    <!-- Folder Documents Panel -->
    <div class="folders">
      <h3>
        Folder Documents
        <button @click="emit('enterChat')" class="enter-chat-btn">
          Enter Chat Mode
        </button>
      </h3>
      <ul>
        <li v-for="doc in savedDocuments" :key="doc">
          <span>{{ doc }}</span>
          <button class="remove-from-folder" @click="emit('toggleFolder', doc)">×</button>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.folders h3 {
  font-family: 'Roboto Condensed', sans-serif;
  color: #274C77;
  margin-bottom: 10px;
}
</style> 
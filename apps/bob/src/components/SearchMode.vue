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
  },
  availableFilters: {
    type: Array,
    required: true
  },
  isSearching: {
    type: Boolean,
    required: true
  }
})

const emit = defineEmits([
  'update:searchQuery',
  'update:selectedFilters',
  'update:currentPage',
  'toggleFolder',
  'enterChat',
  'search'
])

const handleSearch = () => {
  emit('search')
}
</script>

<template>
  <div id="searchMode">
    <!-- Sidebar with Filter Checkboxes -->
    <Filters
      :selectedFilters="selectedFilters"
      :availableFilters="availableFilters"
      @update:selectedFilters="emit('update:selectedFilters', $event)"
    />

    <!-- Main Search and Results Area -->
    <div class="main">
      <div class="search-bar">
        <input 
          type="text" 
          :value="searchQuery"
          @input="emit('update:searchQuery', $event.target.value)"
          @keyup.enter="handleSearch"
          placeholder="What can I help you find?"
        >
        <button 
          @click="handleSearch"
          :disabled="isSearching"
        >
          {{ isSearching ? 'Searching...' : 'Search' }}
        </button>
      </div>

      <div class="results">
        <p class="result-count">{{ documents.length }} document(s) found</p>
        <div v-if="isSearching" class="loading">
          Searching documents...
        </div>
        <div v-else class="search-results">
          <div 
            v-for="item in paginatedResults" 
            :key="item.id"
            class="result-item"
          >
            <div>
              <h3>
                <a 
                  :href="item.source_uri" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  class="title-link"
                >{{ item.title }}</a>
              </h3>
              <p>{{ item.description }}</p>
              <div class="metadata">
                <span class="category" v-if="item.category">{{ item.category }}</span>
                <span class="jurisdiction" v-if="item.jurisdiction && item.jurisdiction !== 'unknown'">
                  {{ item.jurisdiction }}
                </span>
                <span class="score" v-if="item.score">Score: {{ (item.score * 100).toFixed(1) }}%</span>
              </div>
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
            class="pagination-button"
            :disabled="currentPage <= 1"
            @click="emit('update:currentPage', currentPage - 1)"
          >
            <span class="arrow">←</span> Previous
          </button>

          <div class="page-numbers">
            <!-- First page -->
            <button
              v-if="currentPage > 2"
              class="page-number"
              :class="{ active: currentPage === 1 }"
              @click="emit('update:currentPage', 1)"
            >1</button>

            <!-- Ellipsis if needed -->
            <span v-if="currentPage > 3" class="ellipsis">...</span>

            <!-- Previous page if not first -->
            <button
              v-if="currentPage > 1"
              class="page-number"
              @click="emit('update:currentPage', currentPage - 1)"
            >{{ currentPage - 1 }}</button>

            <!-- Current page -->
            <button class="page-number active">{{ currentPage }}</button>

            <!-- Next page if not last -->
            <button
              v-if="currentPage < totalPages"
              class="page-number"
              @click="emit('update:currentPage', currentPage + 1)"
            >{{ currentPage + 1 }}</button>

            <!-- Ellipsis if needed -->
            <span v-if="currentPage < totalPages - 2" class="ellipsis">...</span>

            <!-- Last page -->
            <button
              v-if="currentPage < totalPages - 1"
              class="page-number"
              :class="{ active: currentPage === totalPages }"
              @click="emit('update:currentPage', totalPages)"
            >{{ totalPages }}</button>
          </div>

          <button 
            class="pagination-button"
            :disabled="currentPage >= totalPages"
            @click="emit('update:currentPage', currentPage + 1)"
          >
            Next <span class="arrow">→</span>
          </button>
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
#searchMode {
  display: flex;
  flex: 1;
  overflow: hidden;
  height: 100%;
}

.sidebar {
  width: 220px;
  background-color: #E7ECEF;
  padding: 20px;
  overflow-y: auto;
  flex-shrink: 0;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
  border-left: 1px solid #8B8C89;
  border-right: 1px solid #8B8C89;
  min-width: 0;
  overflow: hidden;
}

.results {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.search-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 80px;
  background-color: #F7F7F7;
  border-bottom: 1px solid #8B8C89;
  padding: 20px;
  gap: 10px;
}

.search-bar input {
  width: 60%;
  padding: 10px;
  font-size: 16px;
  border: 1px solid #8B8C89;
  border-radius: 6px;
}

.search-bar button {
  padding: 10px 20px;
  font-size: 16px;
  background-color: #6096BA;
  border: none;
  border-radius: 6px;
  color: white;
  cursor: pointer;
}

.folders {
  width: 300px;
  background-color: #fff;
  padding: 20px;
  overflow-y: auto;
  border-left: 1px solid #8B8C89;
  flex-shrink: 0;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #6096BA;
  font-style: italic;
}

.metadata {
  margin-top: 0.5rem;
  font-size: 0.9em;
  display: flex;
  gap: 1rem;
}

.category {
  background-color: #E7ECEF;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  color: #274C77;
}

.jurisdiction {
  background-color: #E7ECEF;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  color: #274C77;
}

.score {
  color: #6096BA;
}

.search-bar button:disabled {
  background-color: #8B8C89;
  cursor: not-allowed;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-top: 2rem;
  padding: 1rem;
}

.pagination-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid #6096BA;
  background-color: white;
  color: #6096BA;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s ease;
}

.pagination-button:hover:not(:disabled) {
  background-color: #6096BA;
  color: white;
}

.pagination-button:disabled {
  border-color: #8B8C89;
  color: #8B8C89;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.page-number {
  min-width: 2rem;
  height: 2rem;
  padding: 0 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #E7ECEF;
  background-color: white;
  color: #274C77;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s ease;
}

.page-number:hover:not(.active) {
  border-color: #6096BA;
  background-color: #E7ECEF;
}

.page-number.active {
  background-color: #274C77;
  color: white;
  border-color: #274C77;
  cursor: default;
}

.ellipsis {
  color: #8B8C89;
  padding: 0 0.25rem;
}

.arrow {
  font-size: 1.1rem;
  line-height: 1;
}

.title-link {
  color: #6096BA;
  text-decoration: none;
  transition: color 0.2s ease;
}

.title-link:hover {
  color: #274C77;
  text-decoration: underline;
}

.add-to-folder {
  padding: 0;
  border: none;
  background-color: #274C77;
  color: white;
  cursor: pointer;
  border-radius: 50%;
  font-size: 16px;
  width: 36px;
  height: 36px;
  min-width: 36px;
  min-height: 36px;
  aspect-ratio: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s ease;
}

.add-to-folder.added {
  background-color: #4CAF50;
}

.add-to-folder.added:hover {
  background-color: #FF0000;
}

/* Responsive styles */
@media (max-width: 428px) {
  #searchMode {
    flex-direction: column;
    overflow: auto;
    height: auto;
  }

  .sidebar {
    width: 100%;
    height: auto;
    border-bottom: 1px solid #8B8C89;
  }

  .main {
    flex: none;
    overflow: visible;
    height: auto;
    min-height: 50vh;
  }

  .results {
    overflow: visible;
    height: auto;
    min-height: 200px;
  }

  .search-bar {
    position: sticky;
    top: 0;
    z-index: 10;
    height: auto;
    padding: 15px;
    flex-direction: column;
    gap: 10px;
    background-color: #F7F7F7;
  }

  .search-bar input {
    width: 100%;
    margin: 0;
    height: 44px;
  }

  .search-bar button {
    width: 100%;
    height: 44px;
  }

  .result-item {
    flex-direction: column;
    padding: 15px;
    margin-bottom: 15px;
    border: 1px solid #E7ECEF;
    border-radius: 8px;
    background-color: white;
  }

  .add-to-folder {
    align-self: flex-end;
    margin-top: 10px;
  }

  .folders {
    width: 100%;
    height: auto;
    min-height: 100px;
    border-left: none;
    border-top: 1px solid #8B8C89;
    background-color: white;
  }

  .folders ul {
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .folders li {
    padding: 10px 0;
    border-bottom: 1px solid #E7ECEF;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .folders li:last-child {
    border-bottom: none;
  }

  .result-item h3 {
    margin-bottom: 10px;
  }

  .result-item p {
    margin-bottom: 10px;
  }

  .metadata {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .pagination {
    flex-wrap: wrap;
    gap: 0.5rem;
    padding: 15px;
    margin-top: 1rem;
    background-color: white;
  }

  .page-numbers {
    order: -1;
    width: 100%;
    justify-content: center;
    margin-bottom: 0.5rem;
  }

  .pagination-button {
    flex: 1;
    justify-content: center;
    min-height: 44px;
  }

  .page-number {
    min-width: 44px;
    height: 44px;
    padding: 0;
    font-size: 0.9rem;
  }

  /* Hide some pagination elements on mobile for cleaner look */
  .ellipsis,
  .page-number:not(.active):not(:first-child):not(:last-child) {
    display: none;
  }
}

/* Ensure the app container is full height on mobile */
@media (max-width: 428px) {
  :deep(.app-container) {
    min-height: 100vh;
    height: auto;
  }
}
</style>


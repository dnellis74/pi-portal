<script setup>
import { ref, computed, onMounted } from 'vue'
import './assets/main.css'
import SearchMode from './components/SearchMode.vue'
import ChatMode from './components/ChatMode.vue'
import Header from './components/Header.vue'
import { kendraService } from './services/KendraService'

// State management
const documents = ref([])
const savedDocuments = ref([])
const citations = ref([])
const currentPage = ref(1)
const resultsPerPage = 10
const searchQuery = ref('')
const showChatMode = ref(false)
const chatMessages = ref([])
const chatInput = ref('')
const selectedFilters = ref({
  documentType: [],
  jurisdiction: []
})
const availableFilters = ref({
  documentType: [],
  jurisdiction: []
})
const isSearching = ref(false)

// Computed properties
const paginatedResults = computed(() => {
  const startIndex = (currentPage.value - 1) * resultsPerPage
  const filteredDocs = documents.value.filter(doc => {
    // Check document type filter
    const typeFilters = selectedFilters.value.documentType
    if (typeFilters.length > 0 && !typeFilters.includes(doc.category)) {
      return false
    }

    // Check jurisdiction filter
    const jurisdictionFilters = selectedFilters.value.jurisdiction
    if (jurisdictionFilters.length > 0 && !jurisdictionFilters.includes(doc.jurisdiction)) {
      return false
    }

    return true
  })
  return filteredDocs.slice(startIndex, startIndex + resultsPerPage)
})

const totalPages = computed(() => {
  const filteredDocs = documents.value.filter(doc => {
    // Check document type filter
    const typeFilters = selectedFilters.value.documentType
    if (typeFilters.length > 0 && !typeFilters.includes(doc.category)) {
      return false
    }

    // Check jurisdiction filter
    const jurisdictionFilters = selectedFilters.value.jurisdiction
    if (jurisdictionFilters.length > 0 && !jurisdictionFilters.includes(doc.jurisdiction)) {
      return false
    }

    return true
  })
  return Math.ceil(filteredDocs.length / resultsPerPage)
})

// Methods
const performSearch = async () => {
  if (!searchQuery.value.trim()) return
  
  try {
    isSearching.value = true
    selectedFilters.value = { 
      documentType: [],
      jurisdiction: []
    } // Reset filters
    const results = await kendraService.query(searchQuery.value)
    
    // Map results and extract document types and jurisdictions
    documents.value = results.map(result => ({
      title: result.title,
      description: result.excerpt,
      category: result.documentAttributes?._category?.StringValue || 'uncategorized',
      jurisdiction: result.documentAttributes?.jurisdiction?.StringValue || 'unknown',
      uri: result.uri,
      source_uri: result.documentAttributes?._source_uri?.StringValue || '',
      id: result.id,
      score: result.score
    }))

    // Collect unique document types and jurisdictions for filters
    const uniqueCategories = new Set(
      documents.value
        .map(doc => doc.category)
        .filter(category => category && category !== 'uncategorized')
    )
    const uniqueJurisdictions = new Set(
      documents.value
        .map(doc => doc.jurisdiction)
        .filter(jurisdiction => jurisdiction && jurisdiction !== 'unknown')
    )

    availableFilters.value = {
      documentType: Array.from(uniqueCategories),
      jurisdiction: Array.from(uniqueJurisdictions)
    }
    
    currentPage.value = 1
  } catch (error) {
    console.error('Error performing search:', error)
  } finally {
    isSearching.value = false
  }
}

const toggleFolder = (title) => {
  const index = savedDocuments.value.indexOf(title)
  if (index === -1) {
    savedDocuments.value.push(title)
  } else {
    savedDocuments.value.splice(index, 1)
  }
}

const sendChat = () => {
  if (!chatInput.value.trim()) return
  
  chatMessages.value.push({
    type: 'user',
    text: chatInput.value
  })

  // Simulate bot response with citations
  const response = {
    type: 'bot',
    text: `This is a simulated response referencing the following documents: ${savedDocuments.value.map((_, i) => `<sup>${i+1}</sup>`).join(' ')}`
  }
  chatMessages.value.push(response)

  // Update citations
  citations.value = savedDocuments.value.map((doc, i) => ({
    id: i + 1,
    text: `Citation from "${doc}": "Simulated excerpt from ${doc}."`
  }))

  chatInput.value = ''
}

const enterChatMode = () => {
  if (savedDocuments.value.length === 0) {
    alert("Please add at least one document to the folder first.")
    return
  }
  showChatMode.value = true
}
</script>

<template>
  <div class="app-container">
    <Header :title="showChatMode ? 'Document Chat' : 'Document Search'" />

    <!-- Search Mode -->
    <SearchMode
      v-show="!showChatMode"
      :searchQuery="searchQuery"
      :selectedFilters="selectedFilters"
      :availableFilters="availableFilters"
      :currentPage="currentPage"
      :documents="documents"
      :savedDocuments="savedDocuments"
      :paginatedResults="paginatedResults"
      :totalPages="totalPages"
      :isSearching="isSearching"
      @update:searchQuery="searchQuery = $event"
      @update:selectedFilters="selectedFilters = $event"
      @update:currentPage="currentPage = $event"
      @toggleFolder="toggleFolder"
      @enterChat="enterChatMode"
      @search="performSearch"
    />

    <!-- Chat Mode -->
    <ChatMode
      v-show="showChatMode"
      :savedDocuments="savedDocuments"
      :chatMessages="chatMessages"
      :citations="citations"
      :chatInput="chatInput"
      @update:chatInput="chatInput = $event"
      @toggleFolder="toggleFolder"
      @sendChat="sendChat"
      @backToSearch="showChatMode = false"
    />
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@500&family=Roboto:wght@400&display=swap');
</style>

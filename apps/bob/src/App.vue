<script setup>
import { ref, computed, onMounted } from 'vue'
import './assets/main.css'
import SearchMode from './components/SearchMode.vue'
import ChatMode from './components/ChatMode.vue'
import Header from './components/Header.vue'

// State management
const documents = ref([
  { title: "Air Quality Standards, Designations and Emission Budgets", description: "Regulations on air quality standards and emissions limits.", category: "policy" },
  { title: "Common Provisions Regulation", description: "General provisions for air pollution control regulations.", category: "compliance" },
  { title: "Regulation 7: Control of Emissions from Oil and Gas", description: "Rules for controlling VOC and methane emissions in oil & gas operations.", category: "emissions" },
  { title: "Regulation 9: Open Burning and Prescribed Fire", description: "Guidelines for controlled burns and wildfire management.", category: "ozone" },
  { title: "Regulation 22: Greenhouse Gas Emission Reduction", description: "Statewide greenhouse gas monitoring and reduction plans.", category: "policy" }
])

const savedDocuments = ref([])
const citations = ref([])
const currentPage = ref(1)
const resultsPerPage = 10
const searchQuery = ref('')
const showChatMode = ref(false)
const chatMessages = ref([])
const chatInput = ref('')
const selectedFilters = ref([])

// Computed properties
const filteredDocuments = computed(() => {
  return documents.value.filter(item => {
    const matchesQuery = item.title.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesFilter = selectedFilters.value.length === 0 || selectedFilters.value.includes(item.category)
    return matchesQuery && matchesFilter
  })
})

const paginatedResults = computed(() => {
  const startIndex = (currentPage.value - 1) * resultsPerPage
  return filteredDocuments.value.slice(startIndex, startIndex + resultsPerPage)
})

const totalPages = computed(() => {
  return Math.ceil(filteredDocuments.value.length / resultsPerPage)
})

// Methods
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
      :currentPage="currentPage"
      :documents="documents"
      :savedDocuments="savedDocuments"
      :filteredDocuments="filteredDocuments"
      :paginatedResults="paginatedResults"
      :totalPages="totalPages"
      @update:searchQuery="searchQuery = $event"
      @update:selectedFilters="selectedFilters = $event"
      @update:currentPage="currentPage = $event"
      @toggleFolder="toggleFolder"
      @enterChat="enterChatMode"
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

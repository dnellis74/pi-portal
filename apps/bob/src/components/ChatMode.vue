<script setup>
const props = defineProps({
  savedDocuments: {
    type: Array,
    required: true
  },
  chatMessages: {
    type: Array,
    required: true
  },
  citations: {
    type: Array,
    required: true
  },
  chatInput: {
    type: String,
    required: true
  }
})

const emit = defineEmits([
  'update:chatInput',
  'toggleFolder',
  'sendChat',
  'backToSearch'
])
</script>

<template>
  <div id="chatModeWrapper">
    <div class="chat-container">
      <!-- Left: Folder Documents -->
      <div class="chat-folders">
        <h3>Folder Documents</h3>
        <ul>
          <li v-for="doc in savedDocuments" :key="doc">
            <span>{{ doc }}</span>
            <button class="remove-from-folder" @click="emit('toggleFolder', doc)">×</button>
          </li>
        </ul>
      </div>

      <!-- Middle: Chat Interface -->
      <div class="chat-main">
        <div class="chat-header">
          <h3>Chat with Documents</h3>
          <button class="back-to-search" @click="emit('backToSearch')">
            Back to Search
          </button>
        </div>

        <div class="chat-messages">
          <div 
            v-for="(message, index) in chatMessages" 
            :key="index"
            class="chat-message"
            :class="message.type"
            v-html="message.text"
          ></div>
        </div>

        <div class="chat-input">
          <input 
            type="text" 
            :value="chatInput"
            @input="emit('update:chatInput', $event.target.value)"
            @keyup.enter="emit('sendChat')"
            placeholder="Type your question..."
          >
          <button @click="emit('sendChat')">Send</button>
        </div>
      </div>

      <!-- Right: Citations Panel -->
      <div class="citations-panel">
        <h3>Citations</h3>
        <ul>
          <li v-for="citation in citations" :key="citation.id">
            {{ citation.text }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template> 
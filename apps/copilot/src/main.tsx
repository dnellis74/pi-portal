import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { Amplify } from 'aws-amplify'

// For now, we'll initialize Amplify with minimal configuration
// You'll need to update these values after creating resources in AWS
Amplify.configure({
  Auth: {
    Cognito: {
      identityPoolId: '',
      userPoolClientId: '',
      userPoolId: ''
    }
  }
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

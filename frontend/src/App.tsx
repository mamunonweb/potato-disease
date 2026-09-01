import { BrowserRouter, Route, Routes } from 'react-router'
import { AppShell } from '@/components/app-shell'
import { ChatProvider } from '@/context/chat'
import { PredictionProvider } from '@/context/prediction'
import { ChatPage } from '@/pages/chat'
import { DetectPage } from '@/pages/detect'
import { InfoPage } from '@/pages/info'
import { ResultsPage } from '@/pages/results'

export default function App() {
  return (
    <BrowserRouter>
      <PredictionProvider>
        <ChatProvider>
          <AppShell>
            <Routes>
              <Route path="/" element={<DetectPage />} />
              <Route path="/results" element={<ResultsPage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/info" element={<InfoPage />} />
            </Routes>
          </AppShell>
        </ChatProvider>
      </PredictionProvider>
    </BrowserRouter>
  )
}

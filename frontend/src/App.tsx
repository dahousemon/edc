import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import ChatPage from './pages/ChatPage'
import StaffDashboard from './pages/StaffDashboard'
import LeadsPage from './pages/LeadsPage'
import AnalyticsPage from './pages/AnalyticsPage'
import PropertiesPage from './pages/PropertiesPage'

function App() {
  return (
    <Routes>
      {/* Public chat interface */}
      <Route path="/" element={<ChatPage />} />

      {/* Staff portal */}
      <Route path="/staff" element={<Layout />}>
        <Route index element={<StaffDashboard />} />
        <Route path="leads" element={<LeadsPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="properties" element={<PropertiesPage />} />
      </Route>
    </Routes>
  )
}

export default App

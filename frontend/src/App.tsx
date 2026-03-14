import { Routes, Route } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { DashboardPage } from './pages/DashboardPage'
import { GardensPage } from './pages/GardensPage'
import { CalendarPage } from './pages/CalendarPage'
import { PlantsPage } from './pages/PlantsPage'
import { WeatherPage } from './pages/WeatherPage'
import { AdvisorPage } from './pages/AdvisorPage'
import { AlertsPage } from './pages/AlertsPage'
import { JournalPage } from './pages/JournalPage'
import { SensorsPage } from './pages/SensorsPage'
import { SettingsPage } from './pages/SettingsPage'

const App = (): React.ReactElement => {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/gardens" element={<GardensPage />} />
        <Route path="/calendar" element={<CalendarPage />} />
        <Route path="/plants" element={<PlantsPage />} />
        <Route path="/plants/:id" element={<PlantsPage />} />
        <Route path="/journal" element={<JournalPage />} />
        <Route path="/weather" element={<WeatherPage />} />
        <Route path="/sensors" element={<SensorsPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/advisor" element={<AdvisorPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </AppShell>
  )
}

export default App

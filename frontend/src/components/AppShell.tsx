import { NavLink } from 'react-router-dom'
import {
  Home,
  Calendar,
  Sprout,
  CloudSun,
  Bot,
  Settings,
  Fence,
  BookOpen,
  Bell,
} from 'lucide-react'
import { useGardenStore } from '../stores/gardenStore'
import { useAlertCount } from './AlertPanel'

const navItems = [
  { to: '/', label: 'Dashboard', icon: Home },
  { to: '/gardens', label: 'Gardens', icon: Fence },
  { to: '/plants', label: 'Plants', icon: Sprout },
  { to: '/calendar', label: 'Calendar', icon: Calendar },
  { to: '/journal', label: 'Journal', icon: BookOpen },
  { to: '/weather', label: 'Weather', icon: CloudSun },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/advisor', label: 'Advisor', icon: Bot },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export const AppShell = ({ children }: { children: React.ReactNode }): React.ReactElement => {
  const { selectedGardenId } = useGardenStore()
  const alertCount = useAlertCount(selectedGardenId)

  return (
    <div className="flex h-screen bg-gray-50">
      <nav className="flex flex-col w-56 bg-white border-r border-gray-200 shrink-0">
        <div className="flex items-center gap-2 px-4 py-5 border-b border-gray-200">
          <Sprout className="w-7 h-7 text-green-600" />
          <span className="text-xl font-bold text-gray-900">Verdanta</span>
        </div>
        <ul className="flex-1 px-2 py-4 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-green-50 text-green-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`
                }
              >
                <Icon className="w-5 h-5" />
                {label}
                {label === 'Alerts' && alertCount > 0 && (
                  <span className="ml-auto bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                    {alertCount > 9 ? '9+' : alertCount}
                  </span>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  )
}

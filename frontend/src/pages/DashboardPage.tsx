export const DashboardPage = (): React.ReactElement => {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-sm font-medium text-gray-500 mb-2">Weather</h2>
          <p className="text-gray-400 text-sm">Coming in Phase 3</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-sm font-medium text-gray-500 mb-2">Active Alerts</h2>
          <p className="text-gray-400 text-sm">Coming in Phase 4</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-sm font-medium text-gray-500 mb-2">Today's Tasks</h2>
          <p className="text-gray-400 text-sm">Coming in Phase 3</p>
        </div>
      </div>
    </div>
  )
}

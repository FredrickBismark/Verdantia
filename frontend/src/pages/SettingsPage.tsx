export const SettingsPage = (): React.ReactElement => {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>
      <div className="space-y-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Garden Location</h2>
          <p className="text-gray-400 text-sm">Garden configuration coming in Phase 1 implementation</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">AI Models</h2>
          <p className="text-gray-400 text-sm">LLM provider configuration coming in Phase 2</p>
        </div>
      </div>
    </div>
  )
}

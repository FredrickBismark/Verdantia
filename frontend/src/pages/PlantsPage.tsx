export const PlantsPage = (): React.ReactElement => {
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Plants</h1>
        <button className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors">
          Add Plant
        </button>
      </div>
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <p className="text-gray-400 text-sm">Plant list and detail views coming in Phase 1 implementation</p>
      </div>
    </div>
  )
}

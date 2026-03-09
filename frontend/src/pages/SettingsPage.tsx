import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { settingsApi } from '../api/settings';
import { useGardens } from '../hooks/useGardens';
import { useGardenStore } from '../stores/gardenStore';
import { Save, Check } from 'lucide-react';
import type { AppSetting } from '../types';

export const SettingsPage = (): React.ReactElement => {
  const queryClient = useQueryClient();
  const { data: gardensData } = useGardens();
  const { selectedGardenId, setSelectedGardenId } = useGardenStore();
  const gardens = gardensData?.data ?? [];

  const { data: settingsData } = useQuery({
    queryKey: ['settings'],
    queryFn: () => settingsApi.list(),
  });

  const defaults = useMemo(() => {
    const settingsList = settingsData?.data ?? [];
    const getVal = (key: string): string => {
      const found = settingsList.find((s: AppSetting) => s.key === key);
      return found?.value ?? '';
    };
    return {
      provider: getVal('llm_provider') || 'ollama',
      model: getVal('llm_model') || 'llama3:8b',
    };
  }, [settingsData]);

  const [llmProvider, setLlmProvider] = useState<string | null>(null);
  const [llmModel, setLlmModel] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const currentProvider = llmProvider ?? defaults.provider;
  const currentModel = llmModel ?? defaults.model;

  const updateSetting = useMutation({
    mutationFn: ({ key, value }: { key: string; value: string }) =>
      settingsApi.update(key, value),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
  });

  const handleSaveLLM = (): void => {
    updateSetting.mutate({ key: 'llm_provider', value: currentProvider });
    updateSetting.mutate({ key: 'llm_model', value: currentModel }, {
      onSuccess: () => {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
      },
    });
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>
      <div className="space-y-6 max-w-2xl">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Active Garden</h2>
          <p className="text-sm text-gray-500 mb-3">
            Select which garden is active for dashboard views and plantings.
          </p>
          {gardens.length === 0 ? (
            <p className="text-sm text-gray-400">No gardens created yet. Go to Gardens to create one.</p>
          ) : (
            <select
              value={selectedGardenId ?? ''}
              onChange={(e) => setSelectedGardenId(e.target.value ? parseInt(e.target.value) : null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
            >
              <option value="">Select a garden...</option>
              {gardens.map((g) => (
                <option key={g.id} value={g.id}>{g.name}</option>
              ))}
            </select>
          )}
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">AI Models</h2>
          <p className="text-sm text-gray-500 mb-4">
            Configure which LLM provider and model to use for plant curation and advisor features.
          </p>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
              <select
                value={currentProvider}
                onChange={(e) => setLlmProvider(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              >
                <option value="ollama">Ollama (Local)</option>
                <option value="anthropic">Anthropic</option>
                <option value="openai">OpenAI</option>
                <option value="venice">Venice</option>
                <option value="openrouter">OpenRouter</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
              <input
                type="text"
                value={currentModel}
                onChange={(e) => setLlmModel(e.target.value)}
                placeholder="e.g. llama3:8b"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
            <button
              onClick={handleSaveLLM}
              disabled={updateSetting.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors disabled:opacity-50"
            >
              {saved ? (
                <>
                  <Check className="w-4 h-4" />
                  Saved
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Save Settings
                </>
              )}
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-2">About</h2>
          <div className="text-sm text-gray-500 space-y-1">
            <p>Verdanta v0.1.0</p>
            <p>Garden management with LLM-curated plant intelligence.</p>
            <p>Local-first, privacy-respecting, AI-enhanced.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

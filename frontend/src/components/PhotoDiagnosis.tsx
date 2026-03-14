import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Stethoscope, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { photosApi } from '../api/photos';
import { advisorApi } from '../api/advisor';
import type { PhotoData } from '../api/photos';
import type { DiagnosisResponse } from '../api/advisor';

interface PhotoDiagnosisProps {
  plantingId: number;
}

export const PhotoDiagnosis = ({ plantingId }: PhotoDiagnosisProps): React.ReactElement => {
  const [selectedPhotoId, setSelectedPhotoId] = useState<number | null>(null);
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState<DiagnosisResponse | null>(null);

  const { data: photosData } = useQuery({
    queryKey: ['photos', plantingId],
    queryFn: () => photosApi.list(plantingId, 0, 50),
  });

  const diagnoseMutation = useMutation({
    mutationFn: ({ photoId, question }: { photoId: number; question?: string }) =>
      advisorApi.diagnose(plantingId, photoId, question || null),
    onSuccess: (data) => {
      setResult(data.data);
    },
  });

  const photos: PhotoData[] = photosData?.data ?? [];

  if (photos.length === 0) return <></>;

  return (
    <div className="border border-gray-200 rounded-lg p-4 space-y-3">
      <div className="flex items-center gap-2">
        <Stethoscope className="w-4 h-4 text-purple-600" />
        <h4 className="text-sm font-medium text-gray-700">Photo Diagnosis</h4>
      </div>

      <div className="flex flex-wrap gap-2">
        {photos.map((photo) => (
          <button
            key={photo.id}
            onClick={() => {
              setSelectedPhotoId(photo.id);
              setResult(null);
            }}
            className={`w-16 h-16 rounded-lg overflow-hidden border-2 transition-colors ${
              selectedPhotoId === photo.id ? 'border-purple-500' : 'border-transparent hover:border-gray-300'
            }`}
          >
            <img
              src={photosApi.thumbnailUrl(photo.id)}
              alt={photo.caption ?? 'Photo'}
              className="w-full h-full object-cover"
            />
          </button>
        ))}
      </div>

      {selectedPhotoId && (
        <div className="space-y-2">
          <input
            type="text"
            placeholder="Optional question (e.g. 'What are these spots on the leaves?')"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
          <button
            onClick={() => diagnoseMutation.mutate({ photoId: selectedPhotoId, question })}
            disabled={diagnoseMutation.isPending}
            className="flex items-center gap-2 px-3 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            {diagnoseMutation.isPending ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Analyzing...</>
            ) : (
              <><Stethoscope className="w-4 h-4" /> Diagnose</>
            )}
          </button>
        </div>
      )}

      {diagnoseMutation.isError && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          Diagnosis failed: {(diagnoseMutation.error as Error).message}
        </div>
      )}

      {result && (
        <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
          <div className="prose prose-sm max-w-none text-gray-800">
            <ReactMarkdown>{result.diagnosis}</ReactMarkdown>
          </div>
          <div className="text-xs text-gray-400 mt-3">
            Model: {result.model_used} ({result.provider})
          </div>
        </div>
      )}
    </div>
  );
};

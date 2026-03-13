import { useState, useRef, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, X, Loader2 } from 'lucide-react';
import { photosApi } from '../api/photos';

interface PhotoUploadProps {
  plantingId: number;
}

export const PhotoUpload = ({ plantingId }: PhotoUploadProps): React.ReactElement => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [caption, setCaption] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const uploadMutation = useMutation({
    mutationFn: (file: File) => photosApi.upload(plantingId, file, caption || undefined),
    onSuccess: () => {
      setSelectedFile(null);
      setPreview(null);
      setCaption('');
      void queryClient.invalidateQueries({ queryKey: ['photos', plantingId] });
    },
  });

  const handleFile = useCallback((file: File) => {
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(file);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith('image/')) {
        handleFile(file);
      }
    },
    [handleFile],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback(() => setDragActive(false), []);

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleUpload = (): void => {
    if (selectedFile) {
      uploadMutation.mutate(selectedFile);
    }
  };

  return (
    <div className="space-y-3">
      {!selectedFile ? (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
            dragActive
              ? 'border-green-400 bg-green-50'
              : 'border-gray-300 hover:border-gray-400 bg-gray-50'
          }`}
        >
          <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
          <p className="text-sm text-gray-600">
            Drag & drop a photo here, or <span className="text-green-600 font-medium">browse</span>
          </p>
          <p className="text-xs text-gray-400 mt-1">JPG, PNG, GIF, WebP</p>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex gap-4">
            {preview && (
              <img
                src={preview}
                alt="Preview"
                className="w-24 h-24 object-cover rounded-lg"
              />
            )}
            <div className="flex-1 space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {selectedFile.name}
                </p>
                <button
                  onClick={() => {
                    setSelectedFile(null);
                    setPreview(null);
                  }}
                  className="p-1 text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <input
                type="text"
                placeholder="Caption (optional)"
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
                className="w-full px-3 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-green-400"
              />
              <button
                onClick={handleUpload}
                disabled={uploadMutation.isPending}
                className="px-4 py-1.5 bg-green-600 text-white rounded text-sm font-medium hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
              >
                {uploadMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" /> Uploading...
                  </>
                ) : (
                  'Upload'
                )}
              </button>
            </div>
          </div>
          {uploadMutation.isError && (
            <p className="text-sm text-red-600 mt-2">
              Upload failed: {uploadMutation.error.message}
            </p>
          )}
        </div>
      )}
    </div>
  );
};

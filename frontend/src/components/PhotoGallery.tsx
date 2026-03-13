import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Trash2, Loader2 } from 'lucide-react';
import { photosApi } from '../api/photos';
import type { PhotoData } from '../api/photos';

interface PhotoGalleryProps {
  plantingId: number;
}

export const PhotoGallery = ({ plantingId }: PhotoGalleryProps): React.ReactElement => {
  const queryClient = useQueryClient();
  const [lightboxPhoto, setLightboxPhoto] = useState<PhotoData | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['photos', plantingId],
    queryFn: () => photosApi.list(plantingId),
  });

  const deleteMutation = useMutation({
    mutationFn: (photoId: number) => photosApi.delete(photoId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['photos', plantingId] });
      setLightboxPhoto(null);
    },
  });

  const photos = data?.data ?? [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8 text-gray-400">
        <Loader2 className="w-5 h-5 animate-spin" />
      </div>
    );
  }

  if (photos.length === 0) {
    return (
      <p className="text-sm text-gray-400 text-center py-6">No photos yet.</p>
    );
  }

  return (
    <>
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2">
        {photos.map((photo) => (
          <div key={photo.id} className="relative group aspect-square">
            <img
              src={photosApi.thumbnailUrl(photo.id)}
              alt={photo.caption ?? 'Photo'}
              className="w-full h-full object-cover rounded-lg cursor-pointer"
              onClick={() => setLightboxPhoto(photo)}
            />
            <button
              onClick={(e) => {
                e.stopPropagation();
                deleteMutation.mutate(photo.id);
              }}
              className="absolute top-1 right-1 p-1 bg-black/50 text-white rounded opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
            {photo.caption && (
              <div className="absolute bottom-0 left-0 right-0 bg-black/40 text-white text-xs px-2 py-1 rounded-b-lg truncate">
                {photo.caption}
              </div>
            )}
          </div>
        ))}
      </div>

      {lightboxPhoto && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
          onClick={() => setLightboxPhoto(null)}
        >
          <div className="relative max-w-4xl max-h-[90vh]" onClick={(e) => e.stopPropagation()}>
            <img
              src={photosApi.fileUrl(lightboxPhoto.id)}
              alt={lightboxPhoto.caption ?? 'Photo'}
              className="max-w-full max-h-[85vh] object-contain rounded-lg"
            />
            <div className="absolute top-2 right-2 flex gap-2">
              <button
                onClick={() => deleteMutation.mutate(lightboxPhoto.id)}
                className="p-2 bg-red-600 text-white rounded-full hover:bg-red-700"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              <button
                onClick={() => setLightboxPhoto(null)}
                className="p-2 bg-black/60 text-white rounded-full hover:bg-black/80"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            {lightboxPhoto.caption && (
              <div className="mt-2 text-white text-sm text-center">{lightboxPhoto.caption}</div>
            )}
            <div className="text-gray-400 text-xs text-center mt-1">
              {new Date(lightboxPhoto.taken_at).toLocaleDateString()}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

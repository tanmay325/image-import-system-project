import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});
// Import Functions
export const importFromGoogleDrive = async (folderUrl) => {
  const response = await apiClient.post('/import/google-drive', {
    folder_url: folderUrl,
  });
  return response.data;
};

export const getImportStatus = async (jobId) => {
  const response = await apiClient.get(`/import/status/${jobId}`);
  return response.data;
};

export const getImages = async (page = 1, perPage = 50) => {
  const response = await apiClient.get('/images', {
    params: { page, per_page: perPage },
  });
  return response.data;
};

export const getImage = async (imageId) => {
  const response = await apiClient.get(`/images/${imageId}`);
  return response.data;
};

export const deleteImage = async (imageId) => {
  const response = await apiClient.delete(`/images/${imageId}`);
  return response.data;
};

export const getStats = async () => {
  const response = await apiClient.get('/stats');
  return response.data;
};

const api = {
  importFromGoogleDrive,
  getImportStatus,
  getImages,
  getImage,
  deleteImage,
  getStats,
};

export default api;

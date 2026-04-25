import { apiClient } from './api';

export const memoryService = {
  getProfile: () => apiClient.get('/memory/profile/').then(r => r.data),
  updateProfile: (data) => apiClient.patch('/memory/profile/', data).then(r => r.data),
  list: () => apiClient.get('/memory/list/').then(r => r.data),
  add: (content) => apiClient.post('/memory/list/', { content }).then(r => r.data),
  remove: (id) => apiClient.delete(`/memory/${id}/`),
};

export default memoryService;

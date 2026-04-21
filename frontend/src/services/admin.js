import apiClient from './api';

export const adminService = {
  getStats: () => apiClient.get('/admin/stats/').then(r => r.data),
  getUsers: () => apiClient.get('/admin/users/').then(r => r.data),
  updateUser: (id, data) => apiClient.patch(`/admin/users/${id}/`, data).then(r => r.data),
  deleteUser: (id) => apiClient.delete(`/admin/users/${id}/`),
  getDocuments: () => apiClient.get('/admin/documents/').then(r => r.data),
  deleteDocument: (name) => apiClient.delete(`/admin/documents/${encodeURIComponent(name)}/`),
};

export default adminService;

import { apiClient } from './api';

export const adminService = {
  getStats: () => apiClient.get('/admin/stats/').then(r => r.data),
  getUsers: () => apiClient.get('/admin/users/').then(r => r.data),
  updateUser: (id, data) => apiClient.patch(`/admin/users/${id}/`, data).then(r => r.data),
  deleteUser: (id) => apiClient.delete(`/admin/users/${id}/`),
  getDocuments: () => apiClient.get('/admin/documents/').then(r => r.data),
  deleteDocument: (name) => apiClient.delete(`/admin/documents/${encodeURIComponent(name)}/`),
  uploadDocuments: async (files) => {
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    const res = await apiClient.post('/documents/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  getEvalResults: () => apiClient.get('/admin/eval-results/').then(r => r.data),
  downloadEvalReport: async () => {
    // Fetch the PDF as a blob (auth headers are attached by the apiClient interceptor)
    // and trigger a browser download without needing a public URL.
    const res = await apiClient.get('/admin/eval-report/', { responseType: 'blob' });
    const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Accuracy_Report.pdf';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};

export default adminService;

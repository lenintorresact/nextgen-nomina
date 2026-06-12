import axios from 'axios';

// Descarga un PDF protegido (con token) y dispara la descarga en el navegador.
// Lo usan el Dashboard (reportes consolidados) y la vista del rol individual.
export const downloadPdf = async (
  getToken: () => Promise<string | null>, url: string, filename: string,
) => {
  const token = await getToken();
  const res = await axios.get(url, {
    headers: { Authorization: `Bearer ${token}` }, responseType: 'blob',
  });
  const blobUrl = window.URL.createObjectURL(res.data);
  const a = document.createElement('a');
  a.href = blobUrl;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(blobUrl);
};

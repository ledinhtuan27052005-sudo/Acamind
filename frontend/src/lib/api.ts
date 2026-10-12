import axios from 'axios';

export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
 baseURL: `${API_URL}/api/v1`,
 timeout: 60000,
});

// Inject JWT token into every request
api.interceptors.request.use((config) => {
 if (typeof window !== 'undefined') {
 const token = localStorage.getItem('token');
 if (token) config.headers.Authorization = `Bearer ${token}`;
 }
 return config;
});

// ── Types ─────────────────────────────────────────────────────────────────────

export type UserRole = 'student' | 'researcher' | 'admin' | 'user';

export interface DocumentInfo {
 id: string;
 filename: string;
 title: string | null;
 authors: string | null;
 year: number | null;
 status: 'processing' | 'ready' | 'error';
 total_pages: number | null;
 category: string | null;
 created_at: string | null;
 user_id: string | null;
 is_owner: boolean;
 // Phase A: memory status (built từ document_summaries ở backend)
 has_memory?: boolean;
 memory_status?: 'pending' | 'building' | 'ready' | 'failed' | string;
}

export interface AuthUser {
 id: string;
 email: string;
 full_name: string;
 role: string;
}

export interface QuizQuestion {
 question: string;
 options: string[];
 answer: string;
 explanation: string;
}

export interface EvalResult {
 faithfulness: number;
 answer_relevancy: number;
 context_quality: number;
 feedback: string;
 answer: string;
 sources: { page: number; preview: string }[];
}

// ── Auth APIs ─────────────────────────────────────────────────────────────────

export const sendOtp = async (
 email: string
): Promise<{ message: string; debug_otp?: string }> => {
 const res = await api.post('/auth/send-otp', { email });
 return res.data;
};

export const authRegister = async (
 email: string,
 password: string,
 full_name: string,
 otp: string
): Promise<{ message: string; user_id: string }> => {
 const res = await api.post('/auth/register', { email, password, full_name, otp });
 return res.data;
};

export const authLogin = async (
 email: string,
 password: string
): Promise<{ access_token: string; user: AuthUser }> => {
 const res = await api.post('/auth/login', { email, password });
 return res.data;
};

export const authGoogleLogin = async (
 credential: string
): Promise<{ access_token: string; user: AuthUser }> => {
 const res = await api.post('/auth/google', { credential });
 return res.data;
};

// ── Document APIs ─────────────────────────────────────────────────────────────

export const uploadDocument = async (
 file: File,
 category?: string | null,
 onProgress?: (loaded: number, total: number) => void,
 timeoutMs: number = 600_000, // 10 min for large files
): Promise<{ document_id: string; status: string; message: string }> => {
 const formData = new FormData();
 formData.append('file', file);
 if (category) formData.append('category', category);
 const res = await api.post('/document/upload', formData, {
 headers: { 'Content-Type': 'multipart/form-data' },
 // axios sẽ tự set đúng Content-Type với boundary khi gửi FormData
 // nhưng ta đã khai báo ở trên — giữ để tránh axios tự thêm charset
 onUploadProgress: (e) => {
 if (onProgress && e.total) onProgress(e.loaded, e.total);
 },
 timeout: timeoutMs,
 maxContentLength: Infinity,
 maxBodyLength: Infinity,
 });
 return res.data;
};

export interface DbCategory {
 id: string;
 name: string;
 color: string;
}

export const getCategories = async (): Promise<DbCategory[]> => {
 const res = await api.get('/document/categories');
 return res.data;
};

export const getDocuments = async (): Promise<DocumentInfo[]> => {
 const res = await api.get('/document/list');
 return res.data.documents;
};


export const getDocument = async (id: string): Promise<DocumentInfo> => {
 const res = await api.get(`/document/${id}`);
 return res.data;
};

export const deleteDocument = async (id: string): Promise<void> => {
 await api.delete(`/document/${id}`);
};

export const updateDocumentCategory = async (id: string, category: string | null): Promise<void> => {
 await api.patch(`/document/${id}/category`, { category });
};

export const updateDocumentMetadata = async (
 id: string,
 payload: { title?: string | null; authors?: string | null; year?: number | null },
): Promise<{ title: string | null; authors: string | null; year: number | null }> => {
 const res = await api.patch(`/document/${id}/metadata`, payload);
 return res.data;
};

export const summarizeDocument = async (id: string): Promise<string> => {
 const res = await api.post(`/document/${id}/summarize`);
 return res.data.summary;
};

export const fetchDocumentBlob = async (id: string): Promise<Blob> => {
 const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
 const res = await fetch(`${API_URL}/api/v1/document/${id}/file`, {
 headers: token ? { Authorization: `Bearer ${token}` } : {},
 });
 if (!res.ok) throw new Error('Cannot download PDF file');
 return res.blob();
};

export const lookupDocument = async (query: string): Promise<DocumentInfo | null> => {
  try {
    const res = await api.get('/document/lookup', { params: { q: query } });
    return res.data;
  } catch {
    return null;
  }
};

// ── Plan API ──────────────────────────────────────────────────────────────────

export interface PlanTier {
 key: string;
 label: string;
 price_vnd: number | null;
 max_docs: number | null;
 max_daily_chat: number | null;
 features: string[];
}

export interface PlanUsage {
 plan: string;
 plan_label: string;
 max_docs: number | null;
 max_daily_chat: number | null;
 used_docs: number;
 used_today_chat: number;
}

export const getPricing = async (): Promise<PlanTier[]> => {
 const res = await api.get('/plan/pricing');
 return res.data;
};

export const getMyPlanUsage = async (): Promise<PlanUsage> => {
 const res = await api.get('/plan/me');
 return res.data;
};

export const upgradeUserPlan = async (userId: string, plan: string): Promise<void> => {
 await api.patch(`/plan/users/${userId}`, { plan });
};

// ── Payment APIs ──────────────────────────────────────────────────────────────

export interface PaymentInfo {
 payment_id: string;
 ref_code: string;
 plan: string;
 plan_label: string;
 amount: number;
 bank_code: string;
 bank_account_no: string;
 bank_account_name: string;
 qr_url: string;
 expires_at: string;
 expire_minutes: number;
}

export interface PaymentStatus {
 status: 'pending' | 'completed' | 'expired';
 plan: string;
 amount: number;
 ref_code: string;
 completed_at: string | null;
 expires_at: string;
}

export interface PaymentRecord {
 id: string;
 plan: string;
 plan_label: string;
 amount: number;
 ref_code: string;
 status: 'pending' | 'completed' | 'expired';
 created_at: string | null;
 completed_at: string | null;
}

export const createPayment = async (plan: string): Promise<PaymentInfo> => {
 const res = await api.post('/payment/create', { plan });
 return res.data;
};

export const getPaymentStatus = async (refCode: string): Promise<PaymentStatus> => {
 const res = await api.get(`/payment/status/${refCode}`);
 return res.data;
};

export const getPaymentHistory = async (): Promise<PaymentRecord[]> => {
 const res = await api.get('/payment/history');
 return res.data;
};

export interface AdminPaymentRecord extends PaymentRecord {
 user_id: string;
 user_email: string;
 user_name: string | null;
 expires_at: string;
}

export const adminListPayments = async (status?: string): Promise<AdminPaymentRecord[]> => {
 const res = await api.get('/payment/admin/list', { params: status ? { status } : {} });
 return res.data;
};

export const adminConfirmPayment = async (refCode: string): Promise<{ message: string; ref_code: string }> => {
 const res = await api.post(`/payment/admin/confirm/${refCode}`);
 return res.data;
};

// ── Organization API ──────────────────────────────────────────────────────────

export interface OrgInfo {
 id: string;
 name: string;
 max_slots: number | null;
 max_monthly_docs: number | null;
 member_count: number;
 created_at: string | null;
}

export interface OrgMyInfo {
 role: 'owner' | 'member' | null;
 id?: string;
 name?: string;
 max_slots?: number | null;
 max_monthly_docs?: number | null;
 member_count?: number;
 org_id?: string;
 org_name?: string;
 expires_at?: string;
 duration_label?: string;
 status?: string;
}

export interface OrgInviteCode {
 id: string;
 code: string;
 duration_months: number;
 duration_label: string;
 max_uses: number | null;
 used_count: number;
 valid_until: string | null;
 is_active: boolean;
 created_at: string | null;
}

export interface OrgMember {
 id: string;
 user_id: string;
 user_email: string;
 user_name: string | null;
 duration_label: string;
 joined_at: string | null;
 expires_at: string;
 status: string;
}

export const getMyOrg = async (): Promise<OrgMyInfo> => {
 const res = await api.get('/org/me');
 return res.data;
};

export const createOrg = async (name: string, max_slots?: number): Promise<OrgInfo> => {
 const res = await api.post('/org/create', { name, max_slots });
 return res.data;
};

export const listInviteCodes = async (): Promise<OrgInviteCode[]> => {
 const res = await api.get('/org/invite-codes');
 return res.data;
};

export const createInviteCode = async (
 duration_months: number,
 max_uses?: number,
 valid_days?: number
): Promise<OrgInviteCode> => {
 const res = await api.post('/org/invite-codes', { duration_months, max_uses: max_uses || null, valid_days: valid_days || null });
 return res.data;
};

export const deactivateInviteCode = async (code: string): Promise<void> => {
 await api.delete(`/org/invite-codes/${code}`);
};

export const listOrgMembers = async (): Promise<OrgMember[]> => {
 const res = await api.get('/org/members');
 return res.data;
};

export const kickOrgMember = async (userId: string): Promise<void> => {
 await api.delete(`/org/members/${userId}`);
};

export const updateOrgSettings = async (data: { name?: string; max_slots?: number | null; max_monthly_docs?: number | null }): Promise<OrgInfo> => {
 const res = await api.patch('/org/settings', data);
 return res.data;
};

export const joinOrg = async (code: string): Promise<{ message: string; org_name: string; expires_at: string; duration_label: string }> => {
 const res = await api.post('/org/join', { code });
 return res.data;
};

// ── Notification API ──────────────────────────────────────────────────────────

// ── Library ───────────────────────────────────────────────────────────────────

export interface LibraryArticle {
 id: string;
 document_id: string | null;
 filename: string;
 title_original: string;
 title_vi: string | null;
 authors: string | null;
 year: number | null;
 journal: string | null;
 doi: string | null;
 language: 'en' | 'vi';
 abstract_original: string | null;
 abstract_vi: string | null;
 translation_vi: string | null; // null when locked
 tags: string | null;
 is_paywall: boolean;
 cover_emoji: string | null;
 order_index: number;
 created_at: string;
 translation_locked: boolean;
 pdf_locked: boolean;
}

export async function getLibraryArticles(params?: { search?: string; lang?: string }): Promise<LibraryArticle[]> {
 const res = await api.get('/library/articles', { params });
 return res.data;
}

export async function getLibraryArticle(id: string): Promise<LibraryArticle> {
 const res = await api.get(`/library/articles/${id}`);
 return res.data;
}

export async function fetchLibraryPdf(id: string): Promise<Blob> {
 const res = await api.get(`/library/articles/${id}/pdf`, { responseType: 'blob' });
 return res.data;
}

export async function adminUpdateLibraryArticle(id: string, data: Partial<LibraryArticle>): Promise<LibraryArticle> {
 const res = await api.patch(`/library/admin/articles/${id}`, data);
 return res.data;
}

export async function adminDeleteLibraryArticle(id: string): Promise<void> {
 await api.delete(`/library/admin/articles/${id}`);
}

export interface AppNotification {
 id: string;
 title: string;
 body: string | null;
 type: 'info' | 'success' | 'warning' | 'system';
 is_read: boolean;
 link: string | null;
 created_at: string | null;
}

export const getNotifications = async (): Promise<AppNotification[]> => {
 const res = await api.get('/notification');
 return res.data;
};

export const getUnreadCount = async (): Promise<number> => {
 const res = await api.get('/notification/unread-count');
 return res.data.count;
};

export const markNotifRead = async (id: string): Promise<AppNotification> => {
 const res = await api.patch(`/notification/${id}/read`);
 return res.data;
};

export const markAllNotifsRead = async (): Promise<void> => {
 await api.patch('/notification/read-all');
};

export const deleteNotif = async (id: string): Promise<void> => {
 await api.delete(`/notification/${id}`);
};

export const adminSendNotification = async (data: {
 title: string;
 body?: string;
 type?: string;
 link?: string;
 target_email?: string;
}): Promise<{ ok: boolean; sent_to: number }> => {
 const res = await api.post('/notification/admin/send', data);
 return res.data;
};

// ── Enterprise API ────────────────────────────────────────────────────────────

export interface EnterpriseTicket {
 id: string;
 name: string;
 email: string;
 school_name: string;
 phone: string | null;
 message: string | null;
 status: 'open' | 'in_progress' | 'closed';
 admin_note: string | null;
 user_id: string | null;
 created_at: string | null;
}

export interface EnterpriseOffer {
 id: string;
 ticket_id: string | null;
 token: string;
 school_name: string;
 contact_email: string;
 amount: number;
 duration_months: number;
 package_type: 'monthly' | 'annual';
 max_slots: number | null;
 max_monthly_docs_member: number | null;
 max_monthly_docs_owner: number | null;
 max_annual_docs_owner: number | null;
 ref_code: string;
 status: 'draft' | 'active' | 'paid' | 'expired';
 activated_email: string | null;
 expires_at: string | null;
 created_at: string | null;
 completed_at: string | null;
 offer_url?: string;
}

export interface OfferClaimResult {
 ref_code: string;
 amount: number;
 school_name: string;
 duration_months: number;
 package_type: string;
 bank_code: string;
 bank_account_no: string;
 bank_account_name: string;
 qr_url: string;
 expires_at: string | null;
}

export const submitEnterpriseContact = async (data: {
 name: string;
 email: string;
 school_name: string;
 phone?: string;
 message?: string;
}): Promise<{ ok: boolean; ticket_id: string }> => {
 const res = await api.post('/enterprise/contact', data);
 return res.data;
};

export const getEnterpriseOffer = async (token: string): Promise<EnterpriseOffer> => {
 const res = await api.get(`/enterprise/offer/${token}`);
 return res.data;
};

export const claimEnterpriseOffer = async (token: string, email: string): Promise<OfferClaimResult> => {
 const res = await api.post(`/enterprise/offer/${token}/claim`, { email });
 return res.data;
};

export const pollOfferStatus = async (token: string): Promise<{ status: string; activated_email: string | null }> => {
 const res = await api.get(`/enterprise/offer/${token}/status`);
 return res.data;
};

export const adminListTickets = async (status?: string): Promise<EnterpriseTicket[]> => {
 const res = await api.get('/enterprise/admin/tickets', { params: status ? { status } : {} });
 return res.data;
};

export const adminUpdateTicket = async (
 ticketId: string,
 data: { status?: string; admin_note?: string }
): Promise<EnterpriseTicket> => {
 const res = await api.patch(`/enterprise/admin/tickets/${ticketId}`, data);
 return res.data;
};

export const adminListOffers = async (): Promise<EnterpriseOffer[]> => {
 const res = await api.get('/enterprise/admin/offers');
 return res.data;
};

export const adminCreateOffer = async (data: {
 ticket_id?: string;
 school_name: string;
 contact_email: string;
 amount: number;
 duration_months: number;
 package_type: string;
 max_slots?: number;
 max_monthly_docs_member?: number;
 max_monthly_docs_owner?: number;
 max_annual_docs_owner?: number;
 expires_in_days?: number;
}): Promise<EnterpriseOffer & { offer_url: string }> => {
 const res = await api.post('/enterprise/admin/offers', data);
 return res.data;
};

export const adminConfirmOffer = async (offerId: string): Promise<{ ok: boolean; message: string }> => {
 const res = await api.post(`/enterprise/admin/offers/${offerId}/confirm`);
 return res.data;
};

// ── Psychology API ────────────────────────────────────────────────────────────

export interface PsychologySource {
 doc_title: string;
 doc_authors: string;
 page_number: number | null;
 document_id: string | null;
}

export interface SymptomAnalysisResult {
 analysis: string;
 sources: PsychologySource[];
 chunks_used: number;
}

export interface TreatmentProtocolResult {
 protocol: string;
 sources: PsychologySource[];
 chunks_used: number;
}

export interface CompareSchoolsResult {
 comparison: string;
 sources: PsychologySource[];
 chunks_used: number;
}

export interface TopicSummaryResult {
 summary: string;
 sources: PsychologySource[];
 chunks_used: number;
 topic: string;
}

export const detectQueryDomain = async (
 query: string
): Promise<{ domain: 'psychology' | 'general'; query: string }> => {
 const res = await api.post('/chat/detect-domain', { query });
 return res.data;
};

export const chatGeneralStream = async (
 query: string,
 onChunk: (text: string) => void,
 signal?: AbortSignal
): Promise<void> => {
 const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
 const response = await fetch(`${API_URL}/api/v1/chat/general`, {
 method: 'POST',
 headers: {
 'Content-Type': 'application/json',
 ...(token ? { Authorization: `Bearer ${token}` } : {}),
 },
 body: JSON.stringify({ query }),
 signal,
 });
 if (!response.ok) {
 const errorText = await response.text();
 throw new Error(errorText || `HTTP ${response.status}`);
 }
 const reader = response.body!.getReader();
 const decoder = new TextDecoder('utf-8');
 while (true) {
 const { done, value } = await reader.read();
 if (done) break;
 const text = decoder.decode(value, { stream: true });
 if (text) onChunk(text);
 }
};

export const analyzeSymptoms = async (
 symptomDescription: string,
 documentIds: string[],
 topK?: number
): Promise<SymptomAnalysisResult> => {
 const res = await api.post('/psychology/symptom-analysis', {
 symptom_description: symptomDescription,
 document_ids: documentIds,
 top_k: topK,
 });
 return res.data;
};

export const getTreatmentProtocol = async (
 condition: string,
 documentIds: string[],
 topK?: number
): Promise<TreatmentProtocolResult> => {
 const res = await api.post('/psychology/treatment-protocol', {
 condition,
 document_ids: documentIds,
 top_k: topK,
 });
 return res.data;
};

export const compareSchools = async (
 topic: string,
 documentIds: string[],
 topK?: number
): Promise<CompareSchoolsResult> => {
 const res = await api.post('/psychology/compare-schools', {
 topic,
 document_ids: documentIds,
 top_k: topK,
 });
 return res.data;
};

export const getTopicSummary = async (
 topic: string,
 documentIds: string[],
 topK?: number
): Promise<TopicSummaryResult> => {
 const res = await api.post('/psychology/topic-summary', {
 topic,
 document_ids: documentIds,
 top_k: topK,
 });
 return res.data;
};

// ── Chat API (streaming) ──────────────────────────────────────────────────────

export const chatStream = async (
 query: string,
 documentIds: string[],
 onChunk: (text: string) => void,
 signal?: AbortSignal,
 options?: { forceWebSearch?: boolean }
): Promise<{ noContext: boolean; memoryHit: boolean }> => {
 const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
 const response = await fetch(`${API_URL}/api/v1/chat`, {
 method: 'POST',
 headers: {
 'Content-Type': 'application/json',
 ...(token ? { Authorization: `Bearer ${token}` } : {}),
 },
 body: JSON.stringify({
 query,
 document_ids: documentIds,
 force_web_search: options?.forceWebSearch ?? false,
 }),
 signal,
 });

 if (!response.ok) {
 const errorText = await response.text();
 throw new Error(errorText || `HTTP ${response.status}`);
 }

 // Phase A: đọc X-Memory-Hit header để biết câu trả lời đến từ memory
 // (L1 fast path) hay RAG thường (L2). Frontend dùng để hiển thị badge.
 const memoryHit = response.headers.get('X-Memory-Hit') === 'true';

 // Detect marker __NO_CONTEXT__ ở đầu stream (LLM output khi RAG không tìm được thông tin).
 // Cách xử lý: buffer 100 chars đầu, check marker, nếu có thì yield phần clean (đã strip marker).
 // Sau đó các chunk tiếp theo yield bình thường.
 const reader = response.body!.getReader();
 const decoder = new TextDecoder('utf-8');
 const NO_CONTEXT_MARKER = '__NO_CONTEXT__';
 let header = '';
 let headerChecked = false;
 let noContext = false;

 while (true) {
 const { done, value } = await reader.read();
 if (done) break;
 const text = decoder.decode(value, { stream: true });
 if (!text) continue;

 if (!headerChecked) {
 header += text;
 // Check ngay khi có đủ data (>= 50 chars hoặc thấy marker)
 if (header.includes(NO_CONTEXT_MARKER)) {
 noContext = true;
 headerChecked = true;
 // Strip marker và yield phần clean
 const cleaned = header.replace(NO_CONTEXT_MARKER, '').trimStart();
 if (cleaned) onChunk(cleaned);
 continue;
 }
 if (header.length > 50) {
 // No có marker → yield toàn bộ header đã buffer
 headerChecked = true;
 onChunk(header);
 continue;
 }
 // Chưa đủ data, tiếp tục buffer
 continue;
 }
 onChunk(text);
 }
 // Nếu stream kết thúc mà chưa check header (quá ít data)
 if (!headerChecked && header) onChunk(header);
 return { noContext, memoryHit };
};

export const exportChat = async (
 messages: { role: string; content: string }[],
 title?: string
): Promise<Blob> => {
 const res = await api.post(
  '/chat/export',
  { messages, title: title || 'Academic Q&A Report' },
  { responseType: 'blob' }
 );
 return res.data as Blob;
};

// ── File Chat API ──────────────────────────────────────────────────────────────

export interface ChatFileStreamOptions {
 query: string;
 files: File[];
 documentIds?: string[];
 onChunk: (text: string) => void;
 signal?: AbortSignal;
}

export const chatFileStream = async ({
 query,
 files,
 documentIds = [],
 onChunk,
 signal,
}: ChatFileStreamOptions): Promise<void> => {
 const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
 const formData = new FormData();
 formData.append('query', query);
 formData.append('document_ids', JSON.stringify(documentIds));
 files.forEach((file) => formData.append('files', file));

 const response = await fetch(`${API_URL}/api/v1/chat/file-chat`, {
  method: 'POST',
  headers: {
   ...(token ? { Authorization: `Bearer ${token}` } : {}),
   // NOTE: Do NOT set Content-Type — browser auto-sets multipart boundary
  },
  body: formData,
  signal,
 });

 if (!response.ok) {
  const errorText = await response.text();
  throw new Error(errorText || `HTTP ${response.status}`);
 }

 const reader = response.body!.getReader();
 const decoder = new TextDecoder('utf-8');
 while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const text = decoder.decode(value, { stream: true });
  if (text) onChunk(text);
 }
};

// ── Quiz API ──────────────────────────────────────────────────────────────────

/** Tạo bộ câu hỏi (lưu DB) → trả về quiz_set_id */
export const createQuizSet = async (params: {
 document_id: string;
 num_questions?: number;
 difficulty?: string;
 question_type?: string;
 language?: string;
 user_id?: string;
}): Promise<{ quiz_set_id: string; total_questions: number; title: string; difficulty: string }> => {
 const res = await api.post('/quiz/generate', params);
 return res.data;
};

export interface QuizSetQuestion {
 id: string;
 index: number;
 text: string;
 type: string;
 options: string[];
}

export interface QuizSetData {
 quiz_set_id: string;
 title: string;
 difficulty: string;
 total_questions: number;
 questions: QuizSetQuestion[];
}

/** Lấy câu hỏi theo quiz_set_id (không có đáp án) */
export const getQuizSet = async (quizSetId: string): Promise<QuizSetData> => {
 const res = await api.get(`/quiz/${quizSetId}`);
 return res.data;
};

/** Bắt đầu attempt */
export const startQuizAttempt = async (
 quizSetId: string,
 userId?: string
): Promise<{ attempt_id: string; deadline: string }> => {
 const params = new URLSearchParams({ quiz_set_id: quizSetId });
 if (userId) params.append('user_id', userId);
 const res = await api.post(`/quiz/attempt/start?${params.toString()}`);
 return res.data;
};

/** Save đáp án 1 câu */
export const saveQuizAnswer = async (
 attemptId: string,
 questionId: string,
 userAnswer: string,
 isFlagged = false
): Promise<void> => {
 await api.post('/quiz/answer', {
 attempt_id: attemptId,
 question_id: questionId,
 user_answer: userAnswer,
 is_flagged: isFlagged,
 });
};

export interface QuizReviewItem {
 question: string;
 user_answer: string;
 correct_answer: string;
 is_correct: boolean;
 explanation: string;
}

export interface QuizSubmitResult {
 score: number;
 total_correct: number;
 total_questions: number;
 grade: string;
 time_spent_seconds: number;
 review: QuizReviewItem[];
}

/** Nộp bài + chấm điểm */
export const submitQuizAttempt = async (
 attemptId: string,
 timeSpentSeconds: number
): Promise<QuizSubmitResult> => {
 const res = await api.post('/quiz/attempt/submit', {
 attempt_id: attemptId,
 time_spent_seconds: timeSpentSeconds,
 });
 return res.data;
};


// ── Evaluate API ──────────────────────────────────────────────────────────────

export const runEvaluation = async (
 question: string,
 documentIds: string[]
): Promise<EvalResult> => {
 const res = await api.post('/evaluate/run', { question, document_ids: documentIds });
 return res.data;
};

// ── Stats API ─────────────────────────────────────────────────────────────────

export interface DocStats {
 total_documents: number;
 ready_documents: number;
 processing_documents: number;
 total_chunks: number;
}

export const getDocStats = async (): Promise<DocStats> => {
 const res = await api.get('/document/stats');
 return res.data;
};

export interface SystemReadiness {
 ready_for_rag: boolean;
 llm_configured: boolean;
 llm_model: string;
 ready_documents: number;
 total_chunks: number;
 issues: string[];
}

/** Non-sensitive RAG prerequisites; used to prevent misleading "ready" UI. */
export const getSystemReadiness = async (): Promise<SystemReadiness> => {
 const res = await axios.get(`${API_URL}/health/readiness`, { timeout: 10_000 });
 return res.data;
};

// ── Admin APIs ────────────────────────────────────────────────────────────────

export interface AdminUser {
 id: string;
 email: string;
 full_name: string;
 role: string;
 plan?: string;
 created_at: string | null;
 document_count: number;
}

export interface AdminStats {
 total_users: number;
 admin_count: number;
 researcher_count: number;
 student_count: number;
 pending_applications: number;
 total_documents: number;
 total_chunks: number;
}

export interface ResearcherApplication {
 id: string;
 user_id: string;
 user_email?: string;
 user_name?: string;
 reason: string;
 status: 'pending' | 'approved' | 'rejected';
 admin_note: string | null;
 created_at: string | null;
 reviewed_at: string | null;
}

export const adminListUsers = async (params?: { search?: string; role?: string; plan?: string }): Promise<AdminUser[]> => {
 const res = await api.get('/admin/users', { params });
 return res.data.users;
};

export const adminUpdateRole = async (userId: string, role: string): Promise<void> => {
 await api.patch(`/admin/users/${userId}/role`, { role });
};

export const adminDeleteUser = async (userId: string): Promise<void> => {
 await api.delete(`/admin/users/${userId}`);
};

export const adminGetStats = async (): Promise<AdminStats> => {
 const res = await api.get('/admin/stats');
 return res.data;
};

// ── System settings ───────────────────────────────────────────────────────────

export interface SystemSetting {
 value: string;
 description: string;
 updated_at: string | null;
}

export interface SystemInfo {
 version: string;
 db_status: 'ok' | 'error';
 total_users: number;
 total_documents: number;
 total_chunks: number;
 plan_breakdown: { free: number; pro: number; researcher: number; enterprise: number };
 storage: { user_pdf_count: number; user_pdf_size_mb: number; library_pdf_count: number };
}

export const adminGetSettings = async (): Promise<Record<string, SystemSetting>> => {
 const res = await api.get('/admin/settings');
 return res.data.settings;
};

export const adminUpdateSettings = async (settings: Record<string, string>): Promise<void> => {
 await api.patch('/admin/settings', { settings });
};

export const adminGetSystemInfo = async (): Promise<SystemInfo> => {
 const res = await api.get('/admin/system-info');
 return res.data;
};

export const adminGetPlanLimits = async (): Promise<Record<string, any>> => {
 const res = await api.get('/admin/plan-limits');
 return res.data.plans;
};

export const adminSendTestEmail = async (toEmail: string): Promise<void> => {
 await api.post('/admin/test-email', { to_email: toEmail });
};

export const adminListApplications = async (
 status: 'pending' | 'approved' | 'rejected' = 'pending'
): Promise<ResearcherApplication[]> => {
 const res = await api.get(`/admin/applications?status=${status}`);
 return res.data.applications;
};

export const adminReviewApplication = async (
 appId: string,
 action: 'approve' | 'reject',
 note = ''
): Promise<void> => {
 await api.patch(`/admin/applications/${appId}/review`, { action, note });
};

export interface DocumentCategory {
 id: string;
 name: string;
 color: string;
 doc_count: number;
 created_at: string | null;
}

export const adminListCategories = async (): Promise<DocumentCategory[]> => {
 const res = await api.get('/admin/categories');
 return res.data.categories;
};

export const adminCreateCategory = async (name: string, color: string): Promise<DocumentCategory> => {
 const res = await api.post('/admin/categories', { name, color });
 return res.data;
};

export const adminUpdateCategory = async (
 id: string,
 updates: { name?: string; color?: string }
): Promise<DocumentCategory> => {
 const res = await api.patch(`/admin/categories/${id}`, updates);
 return res.data;
};

export const adminDeleteCategory = async (id: string): Promise<void> => {
 await api.delete(`/admin/categories/${id}`);
};

// ── Researcher Application APIs ───────────────────────────────────────────────

export const applyResearcher = async (reason: string): Promise<{ message: string }> => {
 const res = await api.post('/application/researcher', { reason });
 return res.data;
};

export const getApplicationStatus = async (): Promise<{
 current_role: string;
 status: 'none' | 'pending' | 'approved' | 'rejected';
 application: ResearcherApplication | null;
}> => {
 const res = await api.get('/application/researcher/status');
 return res.data;
};

// ── Graph API ─────────────────────────────────────────────────────────────────

export interface GraphNode {
 id: string;
 type: 'author' | 'document';
 position: { x: number; y: number };
 data: {
 label: string;
 nodeType: string;
 year?: number;
 docId?: string;
 };
}

export interface GraphEdge {
 id: string;
 source: string;
 target: string;
 label: string;
 animated: boolean;
}

export interface GraphData {
 nodes: GraphNode[];
 edges: GraphEdge[];
 stats: { total_authors: number; total_documents: number };
}

export const fetchGraph = async (): Promise<GraphData> => {
 const res = await api.get('/graph');
 return res.data;
};

export const fetchAuthorPapers = async (name: string): Promise<GraphData> => {
 const res = await api.get(`/graph/author/${encodeURIComponent(name)}`);
 return res.data;
};

// ── Body Symptoms API ─────────────────────────────────────────────────────────

export interface SymptomReport {
 user_id?: string;
 region_id: string;
 region_name: string;
 description: string;
 pain_level: number;
 duration?: string | null;
}

export interface SymptomRecord {
 id: string;
 region_id: string;
 region_name: string;
 description: string;
 pain_level: number;
 duration: string | null;
 reported_at: string | null;
}

export const reportSymptom = async (
 report: SymptomReport
): Promise<{ id: string; message: string }> => {
 const res = await api.post('/body/symptoms', report);
 return res.data;
};

export const getUserSymptoms = async (
 userId: string
): Promise<{ total: number; symptoms: SymptomRecord[] }> => {
 const res = await api.get(`/body/symptoms/${userId}`);
 return res.data;
};

export const deleteSymptom = async (symptomId: string): Promise<void> => {
 await api.delete(`/body/symptoms/${symptomId}`);
};

// ── Onboarding API ────────────────────────────────────────────────────────────

export interface OnboardingQuestion {
 id: string;
 question: string;
 options: { value: string; label: string }[];
}

export const getOnboardingQuestions = async (): Promise<{ questions: OnboardingQuestion[] }> => {
 const res = await api.get('/onboarding/questions');
 return res.data;
};

export const submitOnboarding = async (params: {
 user_id?: string;
 answers: Record<string, string>;
}): Promise<{ user_type: string; message: string }> => {
 const res = await api.post('/onboarding/submit', params);
 return res.data;
};

export const getOnboardingStatus = async (
 userId: string
): Promise<{ onboarding_done: boolean; user_type: string }> => {
 const res = await api.get(`/onboarding/status/${userId}`);
 return res.data;
};

// ── Debate API ────────────────────────────────────────────────────────────────

export interface ScrapeResult {
 url: string;
 title: string;
 content: string;
 char_count: number;
}

export const scrapeUrl = async (url: string): Promise<ScrapeResult> => {
 const res = await api.post('/debate/scrape', { url });
 return res.data;
};

export const debateStream = async (
 url1: string,
 url2: string,
 topic: string,
 onChunk: (text: string) => void
): Promise<void> => {
 const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
 const response = await fetch(`${API_URL}/api/v1/debate/analyze`, {
 method: 'POST',
 headers: {
 'Content-Type': 'application/json',
 ...(token ? { Authorization: `Bearer ${token}` } : {}),
 },
 body: JSON.stringify({ url1, url2, topic }),
 });
 if (!response.ok) {
 const errorText = await response.text();
 throw new Error(errorText || `HTTP ${response.status}`);
 }
 const reader = response.body!.getReader();
 const decoder = new TextDecoder('utf-8');
 while (true) {
 const { done, value } = await reader.read();
 if (done) break;
 const text = decoder.decode(value, { stream: true });
 if (text) onChunk(text);
 }
};

// ── Profile Edit APIs ─────────────────────────────────────────────────────────

export interface UserProfile {
 id: string;
 email: string;
 full_name: string;
 role: string;
 plan: string;
 avatar_url: string | null;
 is_oauth: boolean;
}

export const getMyProfile = async (): Promise<UserProfile> => {
 const res = await api.get('/profile/me');
 return res.data;
};

export const updateMyName = async (full_name: string): Promise<{ message: string; full_name: string }> => {
 const res = await api.patch('/profile/me', { full_name });
 return res.data;
};

export const changePassword = async (
 current_password: string,
 new_password: string,
): Promise<{ message: string }> => {
 const res = await api.patch('/profile/password', { current_password, new_password });
 return res.data;
};

export const uploadAvatar = async (file: File): Promise<{ avatar_url: string }> => {
 const formData = new FormData();
 formData.append('file', file);
 const res = await api.post('/profile/avatar', formData, {
 headers: { 'Content-Type': 'multipart/form-data' },
 });
 return res.data;
};

// ── Profile API ───────────────────────────────────────────────────────────────

export interface ChatHistoryRecord {
 id: string;
 query: string;
 answer: string;
 document_ids: string[];
 created_at: string | null;
}

export const saveChatHistory = async (params: {
 user_id?: string;
 query: string;
 answer: string;
 document_ids?: string[];
}): Promise<{ ok: boolean }> => {
 const res = await api.post('/profile/chat-history', params);
 return res.data;
};

export const getChatHistory = async (
 userId: string,
 limit = 20
): Promise<{ total: number; history: ChatHistoryRecord[] }> => {
 const res = await api.get(`/profile/chat-history/${userId}?limit=${limit}`);
 return res.data;
};

export interface ProfileSymptoms {
 total: number;
 avg_pain: number;
 region_counts: Record<string, number>;
 symptoms: SymptomRecord[];
}

export const getProfileSymptoms = async (userId: string): Promise<ProfileSymptoms> => {
 const res = await api.get(`/profile/symptoms/${userId}`);
 return res.data;
};

export interface AIInsight {
 health_insight: string;
 learning_insight: string | null;
 symptom_count: number;
 chat_count: number;
}

export const generateInsights = async (userId: string): Promise<AIInsight> => {
 const res = await api.post(`/profile/insights/${userId}`);
 return res.data;
};

export const getLatestInsight = async (
 userId: string
): Promise<{ insight: string | null; metadata?: Record<string, unknown>; created_at?: string }> => {
 const res = await api.get(`/profile/insights/${userId}/latest`);
 return res.data;
};

export interface ProfileSummary {
 symptom_count: number;
 chat_count: number;
 user_type: string;
 onboarding_done: boolean;
}

export const getProfileSummary = async (userId: string): Promise<ProfileSummary> => {
 const res = await api.get(`/profile/summary/${userId}`);
 return res.data;
};

// ── Authors ───────────────────────────────────────────────────────────────────

export interface AuthorArticleBrief {
 id: string;
 title_original: string;
 title_vi: string | null;
 year: number | null;
 journal: string | null;
 language: 'en' | 'vi';
 is_paywall: boolean;
 cover_emoji: string | null;
}

export interface Author {
 name: string;
 slug: string;
 article_count: number;
 articles: AuthorArticleBrief[];
 year_range: [number, number] | null;
 languages: string[];
}

export interface AuthorDetail {
 name: string;
 slug: string;
 articles: LibraryArticle[];
}

export const getAuthors = async (search?: string): Promise<{ total: number; authors: Author[] }> => {
 const params = new URLSearchParams();
 if (search) params.set('search', search);
 const res = await api.get(`/library/authors${params.toString() ? '?' + params : ''}`);
 return res.data;
};

export const getAuthorDetail = async (slug: string): Promise<AuthorDetail> => {
 const res = await api.get(`/library/authors/${slug}`);
 return res.data;
};

// ── Cross-article analysis ────────────────────────────────────────────────────

export interface AnalysisResult {
 articles: LibraryArticle[];
 analysis: {
 summary: string;
 common_themes: string[];
 differences: string[];
 comparison_table: { factor: string; values: string[] }[];
 research_gaps: string[];
 recommendation: string;
 };
}

export const analyzeArticles = async (articleIds: string[]): Promise<AnalysisResult> => {
 const res = await api.post('/library/analysis', { article_ids: articleIds });
 return res.data;
};

// ── Features ──────────────────────────────────────────────────────────────────

export const translateText = async (text: string, targetLang: 'en' | 'vi', sourceLang = 'auto') => {
 const res = await api.post('/features/translate', { text, target_lang: targetLang, source_lang: sourceLang });
 return res.data as { original: string; translation: string; target_lang: string };
};

export const explainTerm = async (term: string, context?: string, language = 'vi', documentIds?: string[]) => {
 const res = await api.post('/features/explain', { term, context, language, document_ids: documentIds });
 return res.data as { term: string; explanation: string; language: string; source_type?: string; sources?: { doc_title: string; page_number: string | number; text: string }[] };
};

export interface TrendsData {
 total_documents: number;
 keywords: { word: string; count: number }[];
 categories: { name: string; count: number }[];
 years: { year: string; count: number }[];
}
export const getTrends = async (): Promise<TrendsData> => {
 const res = await api.get('/features/trends');
 return res.data;
};

export const generateLiteratureReview = async (documentIds: string[], focus?: string): Promise<Response> => {
 const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
 const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
 return fetch(`${API_URL}/api/v1/features/literature-review`, {
 method: 'POST',
 headers: {
 'Content-Type': 'application/json',
 ...(token ? { Authorization: `Bearer ${token}` } : {}),
 },
 body: JSON.stringify({ document_ids: documentIds, focus }),
 });
};

export interface SlideData {
 document: { id: string; title: string };
 title: string;
 subtitle: string;
 slides: { number: number; title: string; type: string; bullets: string[]; speaker_note: string }[];
 raw?: string;
}
export const generateSlides = async (documentId: string, numSlides = 8, style = 'academic'): Promise<SlideData> => {
 const res = await api.post('/features/slides', { document_id: documentId, num_slides: numSlides, style });
 return res.data;
};

// ── Scientific Appraisal & Evidence-Based Research ─────────────────────────

export interface CebmEvaluation {
  level: string;
  level_label: string;
  grade: string;
  grade_label: string;
  study_design: string;
  stars: string;
  badge_color: string;
  description: string;
}

export interface PicoFramework {
  has_pico: boolean;
  population: string;
  intervention: string;
  comparison: string;
  outcome: string;
  source_type: string;
}

export interface ConsensusMatrix {
  consensus_percentage: number;
  caveats_percentage: number;
  summary: string;
  debate_points: string[];
  consensus_label: string;
}

export interface PeerReviewQuestion {
  title: string;
  critique_point: string;
  question: string;
  category: string;
}

export interface PsychometricScale {
  code: string;
  name: string;
  authors: string;
  items_count: number;
  score_range: string;
  cutoffs: {
    range: string;
    severity: string;
    color: string;
    clinical_action: string;
  }[];
  clinical_threshold: number;
  description: string;
}

export interface KnowledgeGraphData {
  nodes: {
    id: string;
    label: string;
    type: 'disorder' | 'intervention' | 'scale' | 'outcome' | 'document';
    category: string;
    color: string;
  }[];
  edges: {
    source: string;
    target: string;
    label: string;
  }[];
  total_nodes: number;
  total_edges: number;
}

export interface ScientificAppraisal {
  cebm: CebmEvaluation;
  pico: PicoFramework;
  consensus: ConsensusMatrix;
  peer_review_questions: PeerReviewQuestion[];
  detected_scales: PsychometricScale[];
  citations: {
    bibtex: string;
    ris: string;
    apa7: string[];
    docs: { id: string; title: string; authors: string; year: number; filename: string }[];
  };
  knowledge_graph: KnowledgeGraphData;
  total_sources_appraised: number;
}

export const appraiseAnswer = async (
  query: string,
  answer: string,
  documentIds?: string[]
): Promise<ScientificAppraisal> => {
  const res = await api.post('/chat/appraise', {
    query,
    answer,
    document_ids: documentIds || [],
  });
  return res.data;
};

export const exportCitationFile = async (
  format: 'bibtex' | 'ris' | 'apa7',
  documentIds?: string[],
  customDocs?: any[]
): Promise<Blob> => {
  const res = await api.post(
    '/chat/export-citation',
    {
      format,
      document_ids: documentIds || [],
      custom_docs: customDocs || [],
    },
    { responseType: 'blob' }
  );
  return res.data;
};



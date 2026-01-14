import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: Source[]
  feedback?: 'thumbs_up' | 'thumbs_down'
}

export interface Source {
  title: string
  source: string
}

export interface ChatResponse {
  message: string
  conversation_id: string
  message_id: string
  sources: Source[]
  lead_form_requested: boolean
  suggested_actions: string[]
}

export interface Lead {
  id: string
  company_name?: string
  contact_name?: string
  email?: string
  phone?: string
  industry?: string
  space_requirements?: string
  timeline?: string
  score: number
  status: string
  created_at: string
  updated_at: string
}

export interface Property {
  id: string
  name: string
  address: string
  city: string
  state: string
  property_type?: string
  total_sqft?: number
  available_sqft?: number
  price_per_sqft?: number
  lease_rate?: number
  zoning?: string
  features: string[]
  description?: string
  is_available: boolean
}

export interface AnalyticsOverview {
  total_conversations: number
  total_messages: number
  leads_captured: number
  conversion_rate: number
  avg_messages_per_conversation: number
  top_topics: { topic: string; count: number }[]
}

// Chat API
export const chatApi = {
  sendMessage: async (message: string, conversationId?: string): Promise<ChatResponse> => {
    const response = await api.post('/chat/message', {
      message,
      conversation_id: conversationId,
    })
    return response.data
  },

  getConversation: async (conversationId: string) => {
    const response = await api.get(`/chat/conversation/${conversationId}`)
    return response.data
  },

  submitFeedback: async (messageId: string, feedback: 'thumbs_up' | 'thumbs_down') => {
    const response = await api.post('/chat/feedback', {
      message_id: messageId,
      feedback,
    })
    return response.data
  },
}

// Leads API
export const leadsApi = {
  getLeads: async (params?: { status?: string; page?: number; page_size?: number }) => {
    const response = await api.get('/leads', { params })
    return response.data
  },

  getLead: async (leadId: string) => {
    const response = await api.get(`/leads/${leadId}`)
    return response.data
  },

  updateLead: async (leadId: string, updates: Partial<Lead>) => {
    const response = await api.patch(`/leads/${leadId}`, updates)
    return response.data
  },

  getLeadConversation: async (leadId: string) => {
    const response = await api.get(`/leads/${leadId}/conversation`)
    return response.data
  },

  getLeadStats: async () => {
    const response = await api.get('/leads/stats/summary')
    return response.data
  },

  createLead: async (leadData: Partial<Lead>) => {
    const response = await api.post('/leads', leadData)
    return response.data
  },
}

// Properties API
export const propertiesApi = {
  getProperties: async (params?: {
    property_type?: string
    min_sqft?: number
    max_sqft?: number
    page?: number
  }) => {
    const response = await api.get('/properties', { params })
    return response.data
  },

  searchProperties: async (query: string) => {
    const response = await api.post('/properties/search', null, { params: { query } })
    return response.data
  },

  getProperty: async (propertyId: string) => {
    const response = await api.get(`/properties/${propertyId}`)
    return response.data
  },

  getPropertyStats: async () => {
    const response = await api.get('/properties/stats/summary')
    return response.data
  },
}

// Analytics API
export const analyticsApi = {
  getOverview: async (days: number = 30): Promise<AnalyticsOverview> => {
    const response = await api.get('/analytics/overview', { params: { days } })
    return response.data
  },

  getDailyConversations: async (days: number = 30) => {
    const response = await api.get('/analytics/conversations/daily', { params: { days } })
    return response.data
  },

  getLeadFunnel: async (days: number = 30) => {
    const response = await api.get('/analytics/leads/funnel', { params: { days } })
    return response.data
  },

  getFeedbackSummary: async (days: number = 30) => {
    const response = await api.get('/analytics/feedback/summary', { params: { days } })
    return response.data
  },

  getCommonQuestions: async (days: number = 30) => {
    const response = await api.get('/analytics/questions/common', { params: { days } })
    return response.data
  },
}

// Health API
export const healthApi = {
  check: async () => {
    const response = await api.get('/health')
    return response.data
  },

  detailed: async () => {
    const response = await api.get('/health/detailed')
    return response.data
  },
}

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { ThumbsUp, ThumbsDown, TrendingUp, MessageSquare } from 'lucide-react'
import { analyticsApi } from '../services/api'

export default function AnalyticsPage() {
  const [days, setDays] = useState(30)

  const { data: overview } = useQuery({
    queryKey: ['analytics-overview', days],
    queryFn: () => analyticsApi.getOverview(days),
  })

  const { data: dailyData } = useQuery({
    queryKey: ['daily-conversations', days],
    queryFn: () => analyticsApi.getDailyConversations(days),
  })

  const { data: funnel } = useQuery({
    queryKey: ['lead-funnel', days],
    queryFn: () => analyticsApi.getLeadFunnel(days),
  })

  const { data: feedback } = useQuery({
    queryKey: ['feedback-summary', days],
    queryFn: () => analyticsApi.getFeedbackSummary(days),
  })

  const { data: commonQuestions } = useQuery({
    queryKey: ['common-questions', days],
    queryFn: () => analyticsApi.getCommonQuestions(days),
  })

  const funnelData = funnel
    ? [
        { name: 'Conversations', value: funnel.conversations },
        { name: 'Leads Captured', value: funnel.leads_captured },
        { name: 'Contacted', value: funnel.contacted },
        { name: 'Qualified', value: funnel.qualified },
        { name: 'Converted', value: funnel.converted },
      ]
    : []

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-aurora-500"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <MessageSquare className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Conversations</p>
              <p className="text-2xl font-bold">{overview?.total_conversations || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Conversion Rate</p>
              <p className="text-2xl font-bold">{overview?.conversion_rate || 0}%</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-100 rounded-lg">
              <ThumbsUp className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Satisfaction Rate</p>
              <p className="text-2xl font-bold">{feedback?.satisfaction_rate || 0}%</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <MessageSquare className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Avg Messages/Chat</p>
              <p className="text-2xl font-bold">
                {overview?.avg_messages_per_conversation?.toFixed(1) || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Daily conversations chart */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Conversations Over Time</h2>
          <div className="h-[300px]">
            {dailyData?.data?.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={dailyData.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => {
                      const date = new Date(value)
                      return `${date.getMonth() + 1}/${date.getDate()}`
                    }}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="#0284c7"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                No data available
              </div>
            )}
          </div>
        </div>

        {/* Lead funnel */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Lead Funnel</h2>
          <div className="h-[300px]">
            {funnelData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={funnelData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis type="number" tick={{ fontSize: 12 }} />
                  <YAxis dataKey="name" type="category" tick={{ fontSize: 12 }} width={100} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#0284c7" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                No data available
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Common topics */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Common Topics</h2>
          <div className="space-y-3">
            {commonQuestions?.common_topics?.slice(0, 10).map((topic: any, i: number) => (
              <div key={i} className="flex items-center gap-3">
                <div className="flex-1">
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-gray-600 capitalize">{topic.topic}</span>
                    <span className="text-sm text-gray-500">{topic.count}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-aurora-500 h-2 rounded-full"
                      style={{
                        width: `${
                          (topic.count / (commonQuestions?.common_topics?.[0]?.count || 1)) * 100
                        }%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            )) || (
              <p className="text-gray-500 text-center py-4">No data available</p>
            )}
          </div>
        </div>

        {/* Feedback breakdown */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">User Feedback</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-green-50 rounded-lg p-4 text-center">
              <ThumbsUp className="w-8 h-8 text-green-600 mx-auto mb-2" />
              <p className="text-2xl font-bold text-green-700">{feedback?.thumbs_up || 0}</p>
              <p className="text-sm text-green-600">Positive</p>
            </div>
            <div className="bg-red-50 rounded-lg p-4 text-center">
              <ThumbsDown className="w-8 h-8 text-red-600 mx-auto mb-2" />
              <p className="text-2xl font-bold text-red-700">{feedback?.thumbs_down || 0}</p>
              <p className="text-sm text-red-600">Negative</p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Total Feedback</span>
              <span className="font-medium">{feedback?.total_feedback || 0}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

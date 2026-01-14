import { useQuery } from '@tanstack/react-query'
import { Users, MessageSquare, TrendingUp, Building2 } from 'lucide-react'
import { analyticsApi, leadsApi, propertiesApi } from '../services/api'

export default function StaffDashboard() {
  const { data: overview } = useQuery({
    queryKey: ['analytics-overview'],
    queryFn: () => analyticsApi.getOverview(30),
  })

  const { data: leadStats } = useQuery({
    queryKey: ['lead-stats'],
    queryFn: () => leadsApi.getLeadStats(),
  })

  const { data: propertyStats } = useQuery({
    queryKey: ['property-stats'],
    queryFn: () => propertiesApi.getPropertyStats(),
  })

  const { data: recentLeads } = useQuery({
    queryKey: ['recent-leads'],
    queryFn: () => leadsApi.getLeads({ page_size: 5 }),
  })

  const stats = [
    {
      name: 'Total Conversations',
      value: overview?.total_conversations || 0,
      icon: MessageSquare,
      color: 'bg-blue-500',
    },
    {
      name: 'Leads Captured',
      value: overview?.leads_captured || 0,
      icon: Users,
      color: 'bg-green-500',
    },
    {
      name: 'Conversion Rate',
      value: `${overview?.conversion_rate || 0}%`,
      icon: TrendingUp,
      color: 'bg-purple-500',
    },
    {
      name: 'Available Properties',
      value: propertyStats?.total_available || 0,
      icon: Building2,
      color: 'bg-orange-500',
    },
  ]

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
          >
            <div className="flex items-center gap-4">
              <div className={`${stat.color} p-3 rounded-lg`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-500">{stat.name}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Leads */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Leads</h2>
          <div className="space-y-4">
            {recentLeads?.leads?.map((lead: any) => (
              <div
                key={lead.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <p className="font-medium text-gray-900">
                    {lead.company_name || lead.contact_name || 'Unknown'}
                  </p>
                  <p className="text-sm text-gray-500">{lead.industry || 'N/A'}</p>
                </div>
                <div className="text-right">
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      lead.score >= 70
                        ? 'bg-green-100 text-green-700'
                        : lead.score >= 40
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    Score: {lead.score}
                  </span>
                </div>
              </div>
            )) || (
              <p className="text-gray-500 text-center py-4">No leads yet</p>
            )}
          </div>
        </div>

        {/* Top Topics */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Topics</h2>
          <div className="space-y-3">
            {overview?.top_topics?.slice(0, 5).map((topic: any, i: number) => (
              <div key={i} className="flex items-center gap-3">
                <div className="flex-1">
                  <div className="flex justify-between mb-1">
                    <span className="text-sm text-gray-600">{topic.topic}</span>
                    <span className="text-sm text-gray-500">{topic.count}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-aurora-500 h-2 rounded-full"
                      style={{
                        width: `${(topic.count / (overview?.top_topics?.[0]?.count || 1)) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            )) || (
              <p className="text-gray-500 text-center py-4">No data yet</p>
            )}
          </div>
        </div>

        {/* Lead Status Breakdown */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Lead Status</h2>
          <div className="space-y-3">
            {leadStats?.by_status &&
              Object.entries(leadStats.by_status).map(([status, count]: [string, any]) => (
                <div key={status} className="flex items-center justify-between">
                  <span className="text-gray-600 capitalize">{status}</span>
                  <span className="font-medium text-gray-900">{count}</span>
                </div>
              ))}
            {!leadStats?.by_status && (
              <p className="text-gray-500 text-center py-4">No leads yet</p>
            )}
          </div>
        </div>

        {/* Property Types */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Properties by Type</h2>
          <div className="space-y-3">
            {propertyStats?.by_type &&
              Object.entries(propertyStats.by_type).map(([type, count]: [string, any]) => (
                <div key={type} className="flex items-center justify-between">
                  <span className="text-gray-600 capitalize">{type}</span>
                  <span className="font-medium text-gray-900">{count}</span>
                </div>
              ))}
            {!propertyStats?.by_type && (
              <p className="text-gray-500 text-center py-4">No properties yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { Search, Filter, ChevronDown, Mail, Phone, Building2 } from 'lucide-react'
import clsx from 'clsx'
import { leadsApi, Lead } from '../services/api'

const statusColors: Record<string, string> = {
  new: 'bg-blue-100 text-blue-700',
  contacted: 'bg-yellow-100 text-yellow-700',
  qualified: 'bg-purple-100 text-purple-700',
  converted: 'bg-green-100 text-green-700',
  closed: 'bg-gray-100 text-gray-700',
}

export default function LeadsPage() {
  const [selectedStatus, setSelectedStatus] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null)
  const queryClient = useQueryClient()

  const { data: leadsData, isLoading } = useQuery({
    queryKey: ['leads', selectedStatus],
    queryFn: () => leadsApi.getLeads({ status: selectedStatus || undefined, page_size: 50 }),
  })

  const updateLeadMutation = useMutation({
    mutationFn: ({ leadId, updates }: { leadId: string; updates: Partial<Lead> }) =>
      leadsApi.updateLead(leadId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
    },
  })

  const leads = leadsData?.leads || []
  const filteredLeads = leads.filter((lead: Lead) => {
    if (!searchQuery) return true
    const searchLower = searchQuery.toLowerCase()
    return (
      lead.company_name?.toLowerCase().includes(searchLower) ||
      lead.contact_name?.toLowerCase().includes(searchLower) ||
      lead.email?.toLowerCase().includes(searchLower) ||
      lead.industry?.toLowerCase().includes(searchLower)
    )
  })

  const handleStatusChange = (leadId: string, status: string) => {
    updateLeadMutation.mutate({ leadId, updates: { status } })
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Leads</h1>
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search leads..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-aurora-500 focus:border-transparent"
            />
          </div>

          {/* Status filter */}
          <div className="relative">
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="appearance-none pl-4 pr-10 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-aurora-500 focus:border-transparent bg-white"
            >
              <option value="">All Status</option>
              <option value="new">New</option>
              <option value="contacted">Contacted</option>
              <option value="qualified">Qualified</option>
              <option value="converted">Converted</option>
              <option value="closed">Closed</option>
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Leads list */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Lead
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Industry
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Score
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {isLoading ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                      Loading...
                    </td>
                  </tr>
                ) : filteredLeads.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                      No leads found
                    </td>
                  </tr>
                ) : (
                  filteredLeads.map((lead: Lead) => (
                    <tr
                      key={lead.id}
                      onClick={() => setSelectedLead(lead)}
                      className={clsx(
                        'cursor-pointer hover:bg-gray-50 transition-colors',
                        selectedLead?.id === lead.id && 'bg-aurora-50'
                      )}
                    >
                      <td className="px-6 py-4">
                        <div>
                          <p className="font-medium text-gray-900">
                            {lead.company_name || 'Unknown Company'}
                          </p>
                          <p className="text-sm text-gray-500">
                            {lead.contact_name || 'No contact'}
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {lead.industry || 'N/A'}
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={clsx(
                            'inline-flex px-2 py-1 text-xs font-medium rounded-full',
                            lead.score >= 70
                              ? 'bg-green-100 text-green-700'
                              : lead.score >= 40
                              ? 'bg-yellow-100 text-yellow-700'
                              : 'bg-gray-100 text-gray-700'
                          )}
                        >
                          {lead.score}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={clsx(
                            'inline-flex px-2 py-1 text-xs font-medium rounded-full capitalize',
                            statusColors[lead.status] || statusColors.new
                          )}
                        >
                          {lead.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {format(new Date(lead.created_at), 'MMM d, yyyy')}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Lead details panel */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          {selectedLead ? (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Lead Details</h2>

              <div className="space-y-4">
                <div>
                  <label className="text-sm text-gray-500">Company</label>
                  <p className="font-medium text-gray-900">
                    {selectedLead.company_name || 'Not provided'}
                  </p>
                </div>

                <div>
                  <label className="text-sm text-gray-500">Contact</label>
                  <p className="font-medium text-gray-900">
                    {selectedLead.contact_name || 'Not provided'}
                  </p>
                </div>

                {selectedLead.email && (
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-gray-400" />
                    <a
                      href={`mailto:${selectedLead.email}`}
                      className="text-aurora-600 hover:underline"
                    >
                      {selectedLead.email}
                    </a>
                  </div>
                )}

                {selectedLead.phone && (
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-gray-400" />
                    <a
                      href={`tel:${selectedLead.phone}`}
                      className="text-aurora-600 hover:underline"
                    >
                      {selectedLead.phone}
                    </a>
                  </div>
                )}

                {selectedLead.industry && (
                  <div className="flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-900">{selectedLead.industry}</span>
                  </div>
                )}

                <div>
                  <label className="text-sm text-gray-500">Space Requirements</label>
                  <p className="text-gray-900">
                    {selectedLead.space_requirements || 'Not specified'}
                  </p>
                </div>

                <div>
                  <label className="text-sm text-gray-500">Timeline</label>
                  <p className="text-gray-900">
                    {selectedLead.timeline || 'Not specified'}
                  </p>
                </div>

                <div className="pt-4 border-t border-gray-200">
                  <label className="text-sm text-gray-500 block mb-2">Update Status</label>
                  <select
                    value={selectedLead.status}
                    onChange={(e) => handleStatusChange(selectedLead.id, e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-aurora-500"
                  >
                    <option value="new">New</option>
                    <option value="contacted">Contacted</option>
                    <option value="qualified">Qualified</option>
                    <option value="converted">Converted</option>
                    <option value="closed">Closed</option>
                  </select>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              <p>Select a lead to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

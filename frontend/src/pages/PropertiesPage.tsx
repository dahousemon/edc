import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, MapPin, Building, Ruler, DollarSign } from 'lucide-react'
import clsx from 'clsx'
import { propertiesApi, Property } from '../services/api'

export default function PropertiesPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [propertyType, setPropertyType] = useState('')
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null)

  const { data: propertiesData, isLoading } = useQuery({
    queryKey: ['properties', propertyType],
    queryFn: () =>
      propertiesApi.getProperties({
        property_type: propertyType || undefined,
        page_size: 50,
      }),
  })

  const { data: stats } = useQuery({
    queryKey: ['property-stats'],
    queryFn: () => propertiesApi.getPropertyStats(),
  })

  const properties = propertiesData?.properties || []
  const filteredProperties = properties.filter((property: Property) => {
    if (!searchQuery) return true
    const searchLower = searchQuery.toLowerCase()
    return (
      property.name.toLowerCase().includes(searchLower) ||
      property.address.toLowerCase().includes(searchLower) ||
      property.description?.toLowerCase().includes(searchLower)
    )
  })

  const formatNumber = (num: number | undefined) => {
    if (!num) return 'N/A'
    return num.toLocaleString()
  }

  const formatCurrency = (num: number | undefined) => {
    if (!num) return 'N/A'
    return `$${num.toFixed(2)}`
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Properties</h1>
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search properties..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-aurora-500"
            />
          </div>

          {/* Type filter */}
          <select
            value={propertyType}
            onChange={(e) => setPropertyType(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-aurora-500"
          >
            <option value="">All Types</option>
            <option value="industrial">Industrial</option>
            <option value="office">Office</option>
            <option value="retail">Retail</option>
            <option value="warehouse">Warehouse</option>
            <option value="mixed-use">Mixed Use</option>
          </select>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Available Properties</p>
          <p className="text-2xl font-bold text-gray-900">{stats?.total_available || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Total Available Sq Ft</p>
          <p className="text-2xl font-bold text-gray-900">
            {formatNumber(stats?.total_available_sqft)}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Avg Price/Sq Ft</p>
          <p className="text-2xl font-bold text-gray-900">
            {formatCurrency(stats?.avg_price_per_sqft)}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Avg Lease Rate</p>
          <p className="text-2xl font-bold text-gray-900">
            {formatCurrency(stats?.avg_lease_rate)}/sf/yr
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Properties list */}
        <div className="lg:col-span-2 space-y-4">
          {isLoading ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center text-gray-500">
              Loading properties...
            </div>
          ) : filteredProperties.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center text-gray-500">
              No properties found
            </div>
          ) : (
            filteredProperties.map((property: Property) => (
              <div
                key={property.id}
                onClick={() => setSelectedProperty(property)}
                className={clsx(
                  'bg-white rounded-xl shadow-sm border border-gray-200 p-6 cursor-pointer hover:border-aurora-300 transition-colors',
                  selectedProperty?.id === property.id && 'border-aurora-500 ring-1 ring-aurora-500'
                )}
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">{property.name}</h3>
                    <div className="flex items-center gap-1 text-sm text-gray-500 mt-1">
                      <MapPin className="w-4 h-4" />
                      {property.address}, {property.city}, {property.state}
                    </div>
                  </div>
                  <span
                    className={clsx(
                      'px-2 py-1 text-xs font-medium rounded-full capitalize',
                      property.is_available
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-700'
                    )}
                  >
                    {property.is_available ? 'Available' : 'Leased'}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <Building className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-600 capitalize">
                      {property.property_type || 'N/A'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Ruler className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-600">
                      {formatNumber(property.available_sqft)} sq ft
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-600">
                      {property.lease_rate
                        ? `$${property.lease_rate}/sf/yr`
                        : property.price_per_sqft
                        ? `$${property.price_per_sqft}/sf`
                        : 'Contact for pricing'}
                    </span>
                  </div>
                </div>

                {property.features && property.features.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {property.features.slice(0, 4).map((feature, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                      >
                        {feature}
                      </span>
                    ))}
                    {property.features.length > 4 && (
                      <span className="px-2 py-0.5 text-gray-500 text-xs">
                        +{property.features.length - 4} more
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Property details */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 h-fit sticky top-6">
          {selectedProperty ? (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Property Details</h2>

              <div className="space-y-4">
                <div>
                  <label className="text-sm text-gray-500">Name</label>
                  <p className="font-medium text-gray-900">{selectedProperty.name}</p>
                </div>

                <div>
                  <label className="text-sm text-gray-500">Address</label>
                  <p className="text-gray-900">
                    {selectedProperty.address}
                    <br />
                    {selectedProperty.city}, {selectedProperty.state}{' '}
                    {selectedProperty.zip_code}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-500">Type</label>
                    <p className="text-gray-900 capitalize">
                      {selectedProperty.property_type || 'N/A'}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">Zoning</label>
                    <p className="text-gray-900">{selectedProperty.zoning || 'N/A'}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-500">Total Sq Ft</label>
                    <p className="text-gray-900">{formatNumber(selectedProperty.total_sqft)}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">Available Sq Ft</label>
                    <p className="text-gray-900">
                      {formatNumber(selectedProperty.available_sqft)}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-500">Price/Sq Ft</label>
                    <p className="text-gray-900">
                      {formatCurrency(selectedProperty.price_per_sqft)}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">Lease Rate</label>
                    <p className="text-gray-900">
                      {selectedProperty.lease_rate
                        ? `$${selectedProperty.lease_rate}/sf/yr`
                        : 'N/A'}
                    </p>
                  </div>
                </div>

                {selectedProperty.features && selectedProperty.features.length > 0 && (
                  <div>
                    <label className="text-sm text-gray-500">Features</label>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {selectedProperty.features.map((feature, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 bg-aurora-50 text-aurora-700 text-xs rounded"
                        >
                          {feature}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {selectedProperty.description && (
                  <div>
                    <label className="text-sm text-gray-500">Description</label>
                    <p className="text-gray-900 text-sm">{selectedProperty.description}</p>
                  </div>
                )}

                <button className="w-full py-2 bg-aurora-600 text-white rounded-lg hover:bg-aurora-700 transition-colors mt-4">
                  Contact About Property
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              <Building className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p>Select a property to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

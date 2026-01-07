'use client';

import { useEffect, useState } from 'react';
import { erpMappingAPI } from '@/lib/api';
import { ERPModelMapping, ERPModelMappingCreate, ERPModelMappingUpdate } from '@/types';
import { Button } from '@/components/ui/Button';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Toast } from '@/components/ui/Toast';
import { ERPMappingForm } from '@/components/forms/ERPMappingForm';
import { Plus, Edit, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { formatDateShort, handleError } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';

export default function ERPMappingPage() {
  const { user } = useAuth();
  const [mappings, setMappings] = useState<ERPModelMapping[]>([]);
  const [allMappingsData, setAllMappingsData] = useState<ERPModelMapping[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Filter states
  const [manufacturers, setManufacturers] = useState<string[]>([]);
  const [mappedNames, setMappedNames] = useState<string[]>([]);

  const [selectedManufacturer, setSelectedManufacturer] = useState<string>('');
  const [selectedMappedName, setSelectedMappedName] = useState<string>('');

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [totalMappings, setTotalMappings] = useState(0);
  const itemsPerPage = 20;

  // Form states
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [selectedMapping, setSelectedMapping] = useState<ERPModelMapping | undefined>();

  // Delete confirmation states
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [mappingToDelete, setMappingToDelete] = useState<ERPModelMapping | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Toast states
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchAllMappingsData();
    }
  }, [user]);

  useEffect(() => {
    if (selectedManufacturer) {
      updateMappedNames(selectedManufacturer);
    } else {
      setMappedNames([]);
      setSelectedMappedName('');
    }
  }, [selectedManufacturer, allMappingsData]);

  useEffect(() => {
    applyFiltersAndPagination();
  }, [selectedManufacturer, selectedMappedName, currentPage, allMappingsData]);

  const fetchAllMappingsData = async () => {
    try {
      setIsLoading(true);
      // Fetch all data to store locally
      let allData;
      try {
        allData = await erpMappingAPI.getAll({});
      } catch (err) {
        allData = await erpMappingAPI.getAll({ limit: 10000 });
      }

      console.log('Fetched all mappings data:', allData.length, 'records');
      setAllMappingsData(allData);

      // Extract unique manufacturers
      const uniqueManufacturers = Array.from(new Set(allData.map(m => m.manufacturer))).sort();
      console.log('Unique manufacturers:', uniqueManufacturers);
      setManufacturers(uniqueManufacturers);
    } catch (error) {
      console.error('Failed to fetch all mappings data:', error);
      const errorMessage = handleError(error);
      setToast({ message: errorMessage, type: 'error' });
      setAllMappingsData([]);
      setManufacturers([]);
    } finally {
      setIsLoading(false);
    }
  };

  const updateMappedNames = (manufacturer: string) => {
    console.log('Updating mapped names for manufacturer:', manufacturer);
    console.log('All mappings data:', allMappingsData.length);

    // Filter data by manufacturer locally
    const filteredData = allMappingsData.filter(m => m.manufacturer === manufacturer);
    console.log('Filtered data for manufacturer:', filteredData.length, 'records');

    const uniqueMappedNames = Array.from(new Set(filteredData.map(m => m.mapped_name))).sort();
    console.log('Unique mapped names:', uniqueMappedNames);
    setMappedNames(uniqueMappedNames);
  };

  const applyFiltersAndPagination = () => {
    console.log('Applying filters - Manufacturer:', selectedManufacturer, 'Mapped Name:', selectedMappedName);

    // Filter data based on selections
    let filteredData = [...allMappingsData];

    if (selectedManufacturer) {
      filteredData = filteredData.filter(m => m.manufacturer === selectedManufacturer);
    }

    if (selectedMappedName) {
      filteredData = filteredData.filter(m => m.mapped_name === selectedMappedName);
    }

    console.log('Total filtered records:', filteredData.length);

    // Apply pagination
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedData = filteredData.slice(startIndex, endIndex);

    console.log('Paginated records:', paginatedData.length);

    setMappings(paginatedData);
    setTotalMappings(filteredData.length);
  };

  const fetchDropdownData = async () => {
    await fetchAllMappingsData();
  };

  const handleCreate = async (data: ERPModelMappingCreate) => {
    try {
      await erpMappingAPI.create(data);
      setToast({ message: 'Mapping added successfully!', type: 'success' });
      setCurrentPage(1);
      fetchDropdownData();
      fetchAllMappingsData();
      setIsFormOpen(false);
    } catch (error) {
      throw error;
    }
  };

  const handleUpdate = async (data: ERPModelMappingUpdate) => {
    if (!selectedMapping) return;
    try {
      await erpMappingAPI.update(selectedMapping.id, data);
      setToast({ message: 'Mapping updated successfully!', type: 'success' });
      fetchDropdownData();
      fetchAllMappingsData();
      setIsFormOpen(false);
    } catch (error) {
      throw error;
    }
  };

  const handleDelete = async () => {
    if (!mappingToDelete) return;
    try {
      setIsDeleting(true);
      await erpMappingAPI.delete(mappingToDelete.id);
      setToast({ message: 'Mapping deleted successfully!', type: 'success' });
      fetchDropdownData();
      fetchAllMappingsData();
      setIsDeleteDialogOpen(false);
      setMappingToDelete(null);
    } catch (error) {
      setToast({ message: handleError(error), type: 'error' });
    } finally {
      setIsDeleting(false);
    }
  };

  const handleFormSubmit = async (data: ERPModelMappingCreate | ERPModelMappingUpdate) => {
    if (formMode === 'create') {
      await handleCreate(data as ERPModelMappingCreate);
    } else {
      await handleUpdate(data as ERPModelMappingUpdate);
    }
  };

  const handleFilterChange = (
    type: 'manufacturer' | 'mappedName',
    value: string
  ) => {
    setCurrentPage(1);
    if (type === 'manufacturer') {
      setSelectedManufacturer(value);
      // useEffect will handle clearing mapped name
    } else {
      setSelectedMappedName(value);
    }
  };

  const openCreateForm = () => {
    setFormMode('create');
    setSelectedMapping(undefined);
    setIsFormOpen(true);
  };

  const openEditForm = (mapping: ERPModelMapping) => {
    setFormMode('edit');
    setSelectedMapping(mapping);
    setIsFormOpen(true);
  };

  const openDeleteDialog = (mapping: ERPModelMapping) => {
    setMappingToDelete(mapping);
    setIsDeleteDialogOpen(true);
  };

  const totalPages = Math.ceil(totalMappings / itemsPerPage);

  if (user?.role !== 'admin') {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600">This page is only accessible to administrators.</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">ERP Model Mapping</h1>
          <p className="text-sm text-gray-600 mt-1">
            Admin only - Configure ERP model name mappings
          </p>
        </div>
        <Button onClick={openCreateForm}>
          <Plus className="h-4 w-4 mr-2" />
          Add Mapping
        </Button>
      </div>

      {/* Info Card */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <p className="text-sm text-blue-800">
          <strong>Note:</strong> ERP mappings allow you to map internal ERP model names to standard model names
          for consistent data processing and reporting.
        </p>
      </div>

      {/* Filter Dropdowns */}
      <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Manufacturer Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Manufacturer
          </label>
          <select
            value={selectedManufacturer}
            onChange={(e) => handleFilterChange('manufacturer', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Manufacturers</option>
            {manufacturers.map((manufacturer) => (
              <option key={manufacturer} value={manufacturer}>
                {manufacturer}
              </option>
            ))}
          </select>
        </div>

        {/* Mapped Name Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Mapped Name
          </label>
          <select
            value={selectedMappedName}
            onChange={(e) => handleFilterChange('mappedName', e.target.value)}
            disabled={!selectedManufacturer}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="">
              {selectedManufacturer ? 'All Mapped Names' : 'Select Manufacturer First'}
            </option>
            {mappedNames.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Manufacturer
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ERP Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Mapped Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Updated
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {mappings.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                    No mappings found matching the selected filters.
                  </td>
                </tr>
              ) : (
                mappings.map((mapping) => (
                  <tr key={mapping.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {mapping.manufacturer}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-3 py-1 text-xs font-medium bg-purple-100 text-purple-800 rounded-full">
                        {mapping.erp_name}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-3 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                        {mapping.mapped_name}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDateShort(mapping.updated_date)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => openEditForm(mapping)}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                        title="Edit"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => openDeleteDialog(mapping)}
                        className="text-red-600 hover:text-red-900"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      <div className="mt-4 flex items-center justify-between">
        <div className="text-sm text-gray-600">
          Showing {mappings.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0} to{' '}
          {Math.min(currentPage * itemsPerPage, totalMappings)} of {totalMappings} mappings
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
            disabled={currentPage === 1}
            variant="secondary"
            size="sm"
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </Button>
          <div className="flex items-center px-4 py-2 text-sm text-gray-700">
            Page {currentPage} of {totalPages || 1}
          </div>
          <Button
            onClick={() => setCurrentPage((prev) => prev + 1)}
            disabled={currentPage >= totalPages || mappings.length < itemsPerPage}
            variant="secondary"
            size="sm"
          >
            Next
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </div>

      {/* Example Mappings */}
      <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Example Mappings:</h3>
        <div className="text-xs text-gray-600 space-y-1">
          <p>• Toyota - CRL → Corolla</p>
          <p>• Honda - CVC → Civic</p>
          <p>• Nissan - MRC → March</p>
        </div>
      </div>

      {/* Create/Edit Form */}
      <ERPMappingForm
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
        mapping={selectedMapping}
        mode={formMode}
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        onConfirm={handleDelete}
        title="Delete Mapping"
        message={`Are you sure you want to delete the mapping: ${mappingToDelete?.manufacturer} - ${mappingToDelete?.erp_name} → ${mappingToDelete?.mapped_name}? This action cannot be undone.`}
        confirmText="Delete"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  );
}

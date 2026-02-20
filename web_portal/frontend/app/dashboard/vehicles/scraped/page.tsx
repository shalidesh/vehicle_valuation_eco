'use client';

import { useEffect, useState } from 'react';
import { summaryStatisticsAPI, analyticsAPI } from '@/lib/api';
import { SummaryStatistic, SummaryStatisticCreate, SummaryStatisticUpdate } from '@/types';
import { Button } from '@/components/ui/Button';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Toast } from '@/components/ui/Toast';
import { SummaryStatisticForm } from '@/components/forms/ScrapedVehicleForm';
import { Plus, Edit, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { formatCurrency, handleError } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';

export default function SummaryStatisticsPage() {
  const { user } = useAuth();
  const [records, setRecords] = useState<SummaryStatistic[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Filter states
  const [manufacturers, setManufacturers] = useState<string[]>([]);
  const [models, setModels] = useState<string[]>([]);
  const [years, setYears] = useState<string[]>([]);

  const [selectedManufacturer, setSelectedManufacturer] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [selectedYear, setSelectedYear] = useState<string>('');
  const [selectedTransmission, setSelectedTransmission] = useState<string>('');
  const [selectedFuelType, setSelectedFuelType] = useState<string>('');

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);
  const itemsPerPage = 20;

  // Form states
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [selectedRecord, setSelectedRecord] = useState<SummaryStatistic | undefined>();

  // Delete confirmation states
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [recordToDelete, setRecordToDelete] = useState<SummaryStatistic | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Toast states
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchManufacturers();
    }
  }, [user]);

  useEffect(() => {
    if (selectedManufacturer) {
      fetchModels(selectedManufacturer);
    } else {
      setModels([]);
      setSelectedModel('');
    }
  }, [selectedManufacturer]);

  useEffect(() => {
    if (selectedManufacturer && selectedModel) {
      fetchYears(selectedManufacturer, selectedModel);
    } else {
      setYears([]);
      setSelectedYear('');
    }
  }, [selectedManufacturer, selectedModel]);

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchRecords();
    }
  }, [selectedManufacturer, selectedModel, selectedYear, selectedTransmission, selectedFuelType, currentPage, user]);

  const fetchManufacturers = async () => {
    try {
      const manufacturersData = await analyticsAPI.getManufacturers('summary');
      setManufacturers(manufacturersData.sort());
    } catch (error) {
      console.error('Failed to fetch manufacturers:', error);
      const errorMessage = handleError(error);
      setToast({ message: errorMessage, type: 'error' });
    }
  };

  const fetchModels = async (manufacturer: string) => {
    try {
      const modelsData = await analyticsAPI.getModels(manufacturer, 'summary');
      setModels(modelsData.sort());
    } catch (error) {
      console.error('Failed to fetch models:', error);
      const errorMessage = handleError(error);
      setToast({ message: errorMessage, type: 'error' });
    }
  };

  const fetchYears = async (manufacturer: string, model: string) => {
    try {
      const yearsData = await analyticsAPI.getYears(manufacturer, model, 'summary');
      setYears(yearsData.map(String).sort((a, b) => b.localeCompare(a)));
    } catch (error) {
      console.error('Failed to fetch years:', error);
      const errorMessage = handleError(error);
      setToast({ message: errorMessage, type: 'error' });
    }
  };

  const fetchDropdownData = async () => {
    await fetchManufacturers();
    if (selectedManufacturer) {
      await fetchModels(selectedManufacturer);
      if (selectedModel) {
        await fetchYears(selectedManufacturer, selectedModel);
      }
    }
  };

  const fetchRecords = async () => {
    try {
      setIsLoading(true);
      const skip = (currentPage - 1) * itemsPerPage;
      const params: any = {
        skip,
        limit: itemsPerPage,
      };

      if (selectedManufacturer) params.make = selectedManufacturer;
      if (selectedModel) params.model = selectedModel;
      if (selectedYear) params.yom = selectedYear;
      if (selectedTransmission) params.transmission = selectedTransmission;
      if (selectedFuelType) params.fuel_type = selectedFuelType;

      const data = await summaryStatisticsAPI.getAll(params);
      setRecords(data);
      setTotalRecords(data.length < itemsPerPage ? skip + data.length : skip + itemsPerPage + 1);
    } catch (error) {
      console.error('Failed to fetch records:', error);
      const errorMessage = handleError(error);
      setToast({ message: errorMessage, type: 'error' });
      setRecords([]);
      setTotalRecords(0);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = async (data: SummaryStatisticCreate) => {
    try {
      await summaryStatisticsAPI.create(data);
      setToast({ message: 'Summary statistic added successfully!', type: 'success' });
      setCurrentPage(1);
      fetchDropdownData();
      fetchRecords();
      setIsFormOpen(false);
    } catch (error) {
      throw error;
    }
  };

  const handleUpdate = async (data: SummaryStatisticUpdate) => {
    if (!selectedRecord) return;
    try {
      await summaryStatisticsAPI.update(
        {
          make: selectedRecord.make,
          model: selectedRecord.model,
          yom: selectedRecord.yom,
          transmission: selectedRecord.transmission,
          fuel_type: selectedRecord.fuel_type,
        },
        data
      );
      setToast({ message: 'Summary statistic updated successfully!', type: 'success' });
      fetchDropdownData();
      fetchRecords();
      setIsFormOpen(false);
    } catch (error) {
      throw error;
    }
  };

  const handleDelete = async () => {
    if (!recordToDelete) return;
    try {
      setIsDeleting(true);
      await summaryStatisticsAPI.delete({
        make: recordToDelete.make,
        model: recordToDelete.model,
        yom: recordToDelete.yom,
        transmission: recordToDelete.transmission,
        fuel_type: recordToDelete.fuel_type,
      });
      setToast({ message: 'Summary statistic deleted successfully!', type: 'success' });
      fetchDropdownData();
      fetchRecords();
      setIsDeleteDialogOpen(false);
      setRecordToDelete(null);
    } catch (error) {
      setToast({ message: handleError(error), type: 'error' });
    } finally {
      setIsDeleting(false);
    }
  };

  const handleFormSubmit = async (data: SummaryStatisticCreate | SummaryStatisticUpdate) => {
    if (formMode === 'create') {
      await handleCreate(data as SummaryStatisticCreate);
    } else {
      await handleUpdate(data as SummaryStatisticUpdate);
    }
  };

  const handleFilterChange = (
    type: 'manufacturer' | 'model' | 'year' | 'transmission' | 'fuel_type',
    value: string
  ) => {
    setCurrentPage(1);
    if (type === 'manufacturer') {
      setSelectedManufacturer(value);
    } else if (type === 'model') {
      setSelectedModel(value);
    } else if (type === 'year') {
      setSelectedYear(value);
    } else if (type === 'transmission') {
      setSelectedTransmission(value);
    } else if (type === 'fuel_type') {
      setSelectedFuelType(value);
    }
  };

  const openCreateForm = () => {
    setFormMode('create');
    setSelectedRecord(undefined);
    setIsFormOpen(true);
  };

  const openEditForm = (record: SummaryStatistic) => {
    setFormMode('edit');
    setSelectedRecord(record);
    setIsFormOpen(true);
  };

  const openDeleteDialog = (record: SummaryStatistic) => {
    setRecordToDelete(record);
    setIsDeleteDialogOpen(true);
  };

  const totalPages = Math.ceil(totalRecords / itemsPerPage);

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
          <h1 className="text-3xl font-bold text-gray-900">Summary Statistics</h1>
          <p className="text-sm text-gray-600 mt-1">
            Admin only - Manage pre-computed average price statistics
          </p>
        </div>
        <Button onClick={openCreateForm}>
          <Plus className="h-4 w-4 mr-2" />
          Add Record
        </Button>
      </div>

      {/* Filter Dropdowns */}
      <div className="mb-6 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {/* Manufacturer Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Make
          </label>
          <select
            value={selectedManufacturer}
            onChange={(e) => handleFilterChange('manufacturer', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Makes</option>
            {manufacturers.map((manufacturer) => (
              <option key={manufacturer} value={manufacturer}>
                {manufacturer}
              </option>
            ))}
          </select>
        </div>

        {/* Model Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Model
          </label>
          <select
            value={selectedModel}
            onChange={(e) => handleFilterChange('model', e.target.value)}
            disabled={!selectedManufacturer}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="">
              {selectedManufacturer ? 'All Models' : 'Select Make First'}
            </option>
            {models.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </div>

        {/* Year Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            YOM
          </label>
          <select
            value={selectedYear}
            onChange={(e) => handleFilterChange('year', e.target.value)}
            disabled={!selectedModel}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="">
              {selectedModel ? 'All Years' : 'Select Model First'}
            </option>
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </div>

        {/* Transmission Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Transmission
          </label>
          <select
            value={selectedTransmission}
            onChange={(e) => handleFilterChange('transmission', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All</option>
            <option value="Automatic">Automatic</option>
            <option value="Manual">Manual</option>
            <option value="CVT">CVT</option>
          </select>
        </div>

        {/* Fuel Type Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Fuel Type
          </label>
          <select
            value={selectedFuelType}
            onChange={(e) => handleFilterChange('fuel_type', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All</option>
            <option value="Petrol">Petrol</option>
            <option value="Diesel">Diesel</option>
            <option value="Hybrid">Hybrid</option>
            <option value="Electric">Electric</option>
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
                  Make
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Model
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  YOM
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Transmission
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fuel Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Average Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Updated Date
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {records.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                    No records found matching the selected filters.
                  </td>
                </tr>
              ) : (
                records.map((record, index) => (
                  <tr key={`${record.make}-${record.model}-${record.yom}-${record.transmission}-${record.fuel_type}`} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {record.make}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {record.model}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {record.yom}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {record.transmission || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {record.fuel_type || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(record.average_price)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {record.updated_date || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => openEditForm(record)}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                        title="Edit"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => openDeleteDialog(record)}
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
          Showing {records.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0} to{' '}
          {Math.min(currentPage * itemsPerPage, totalRecords)} of {totalRecords} records
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
            disabled={currentPage >= totalPages || records.length < itemsPerPage}
            variant="secondary"
            size="sm"
          >
            Next
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </div>

      {/* Create/Edit Form */}
      <SummaryStatisticForm
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
        record={selectedRecord}
        mode={formMode}
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        onConfirm={handleDelete}
        title="Delete Summary Statistic"
        message={`Are you sure you want to delete ${recordToDelete?.make} ${recordToDelete?.model} (${recordToDelete?.yom})? This action cannot be undone.`}
        confirmText="Delete"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  );
}

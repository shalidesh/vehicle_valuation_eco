'use client';

import { useEffect, useState } from 'react';
import { scrapedVehiclesAPI, analyticsAPI } from '@/lib/api';
import { ScrapedVehicle, ScrapedVehicleCreate, ScrapedVehicleUpdate } from '@/types';
import { Button } from '@/components/ui/Button';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Toast } from '@/components/ui/Toast';
import { ScrapedVehicleForm } from '@/components/forms/ScrapedVehicleForm';
import { Plus, Edit, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { formatCurrency, formatDateShort, handleError } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';

export default function ScrapedVehiclesPage() {
  const { user } = useAuth();
  const [vehicles, setVehicles] = useState<ScrapedVehicle[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Filter states
  const [manufacturers, setManufacturers] = useState<string[]>([]);
  const [models, setModels] = useState<string[]>([]);
  const [years, setYears] = useState<number[]>([]);

  const [selectedType, setSelectedType] = useState<string>('');
  const [selectedManufacturer, setSelectedManufacturer] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [selectedYear, setSelectedYear] = useState<string>('');

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [totalVehicles, setTotalVehicles] = useState(0);
  const itemsPerPage = 20;

  // Form states
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [selectedVehicle, setSelectedVehicle] = useState<ScrapedVehicle | undefined>();

  // Delete confirmation states
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [vehicleToDelete, setVehicleToDelete] = useState<ScrapedVehicle | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Toast states
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchManufacturers();
    }
  }, [user, selectedType]);

  useEffect(() => {
    if (selectedManufacturer) {
      fetchModels(selectedManufacturer);
    } else {
      setModels([]);
      setSelectedModel('');
    }
  }, [selectedManufacturer, selectedType]);

  useEffect(() => {
    if (selectedManufacturer && selectedModel) {
      fetchYears(selectedManufacturer, selectedModel);
    } else {
      setYears([]);
      setSelectedYear('');
    }
  }, [selectedManufacturer, selectedModel, selectedType]);

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchVehicles();
    }
  }, [selectedType, selectedManufacturer, selectedModel, selectedYear, currentPage, user]);

  const fetchManufacturers = async () => {
    try {
      const manufacturersData = await analyticsAPI.getManufacturers('scraped', selectedType || undefined);
      setManufacturers(manufacturersData.sort());
    } catch (error) {
      console.error('Failed to fetch manufacturers:', error);
      const errorMessage = handleError(error);
      setToast({ message: errorMessage, type: 'error' });
    }
  };

  const fetchModels = async (manufacturer: string) => {
    try {
      const modelsData = await analyticsAPI.getModels(manufacturer, 'scraped', selectedType || undefined);
      setModels(modelsData.sort());
    } catch (error) {
      console.error('Failed to fetch models:', error);
      const errorMessage = handleError(error);
      setToast({ message: errorMessage, type: 'error' });
    }
  };

  const fetchYears = async (manufacturer: string, model: string) => {
    try {
      const yearsData = await analyticsAPI.getYears(manufacturer, model, 'scraped', selectedType || undefined);
      setYears(yearsData.sort((a, b) => b - a));
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

  const fetchVehicles = async () => {
    try {
      setIsLoading(true);
      const skip = (currentPage - 1) * itemsPerPage;
      const params: any = {
        skip,
        limit: itemsPerPage,
      };

      if (selectedType) params.vehicle_type = selectedType;
      if (selectedManufacturer) params.manufacturer = selectedManufacturer;
      if (selectedModel) params.model = selectedModel;
      if (selectedYear) params.yom = parseInt(selectedYear);

      const data = await scrapedVehiclesAPI.getAll(params);
      setVehicles(data);
      setTotalVehicles(data.length < itemsPerPage ? skip + data.length : skip + itemsPerPage + 1);
    } catch (error) {
      console.error('Failed to fetch vehicles:', error);
      const errorMessage = handleError(error);
      setToast({ message: errorMessage, type: 'error' });
      setVehicles([]);
      setTotalVehicles(0);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = async (data: ScrapedVehicleCreate) => {
    try {
      await scrapedVehiclesAPI.create(data);
      setToast({ message: 'Vehicle added successfully!', type: 'success' });
      setCurrentPage(1);
      fetchDropdownData();
      fetchVehicles();
      setIsFormOpen(false);
    } catch (error) {
      throw error;
    }
  };

  const handleUpdate = async (data: ScrapedVehicleUpdate) => {
    if (!selectedVehicle) return;
    try {
      await scrapedVehiclesAPI.update(selectedVehicle.id, data);
      setToast({ message: 'Vehicle updated successfully!', type: 'success' });
      fetchDropdownData();
      fetchVehicles();
      setIsFormOpen(false);
    } catch (error) {
      throw error;
    }
  };

  const handleDelete = async () => {
    if (!vehicleToDelete) return;
    try {
      setIsDeleting(true);
      await scrapedVehiclesAPI.delete(vehicleToDelete.id);
      setToast({ message: 'Vehicle deleted successfully!', type: 'success' });
      fetchDropdownData();
      fetchVehicles();
      setIsDeleteDialogOpen(false);
      setVehicleToDelete(null);
    } catch (error) {
      setToast({ message: handleError(error), type: 'error' });
    } finally {
      setIsDeleting(false);
    }
  };

  const handleFormSubmit = async (data: ScrapedVehicleCreate | ScrapedVehicleUpdate) => {
    if (formMode === 'create') {
      await handleCreate(data as ScrapedVehicleCreate);
    } else {
      await handleUpdate(data as ScrapedVehicleUpdate);
    }
  };

  const handleFilterChange = (
    type: 'type' | 'manufacturer' | 'model' | 'year',
    value: string
  ) => {
    setCurrentPage(1);
    if (type === 'type') {
      setSelectedType(value);
    } else if (type === 'manufacturer') {
      setSelectedManufacturer(value);
    } else if (type === 'model') {
      setSelectedModel(value);
    } else {
      setSelectedYear(value);
    }
  };

  const openCreateForm = () => {
    setFormMode('create');
    setSelectedVehicle(undefined);
    setIsFormOpen(true);
  };

  const openEditForm = (vehicle: ScrapedVehicle) => {
    setFormMode('edit');
    setSelectedVehicle(vehicle);
    setIsFormOpen(true);
  };

  const openDeleteDialog = (vehicle: ScrapedVehicle) => {
    setVehicleToDelete(vehicle);
    setIsDeleteDialogOpen(true);
  };

  const totalPages = Math.ceil(totalVehicles / itemsPerPage);

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
          <h1 className="text-3xl font-bold text-gray-900">Scraped Vehicles</h1>
          <p className="text-sm text-gray-600 mt-1">
            Admin only - Manage scraped vehicle data with price history
          </p>
        </div>
        <Button onClick={openCreateForm}>
          <Plus className="h-4 w-4 mr-2" />
          Add Vehicle
        </Button>
      </div>

      {/* Filter Dropdowns */}
      <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Type Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Type
          </label>
          <select
            value={selectedType}
            onChange={(e) => handleFilterChange('type', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Types</option>
            <option value="REGISTERED">Registered</option>
            <option value="UNREGISTERED">Unregistered</option>
          </select>
        </div>

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
              {selectedManufacturer ? 'All Models' : 'Select Manufacturer First'}
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
            Year
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
              <option key={year} value={year.toString()}>
                {year}
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
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Manufacturer
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Model
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Year
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Transmission
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fuel Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Mileage
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Price
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
              {vehicles.length === 0 ? (
                <tr>
                  <td colSpan={10} className="px-6 py-4 text-center text-gray-500">
                    No vehicles found matching the selected filters.
                  </td>
                </tr>
              ) : (
                vehicles.map((vehicle) => (
                  <tr key={vehicle.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        vehicle.type === 'REGISTERED'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {vehicle.type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {vehicle.manufacturer}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {vehicle.model}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {vehicle.yom}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {vehicle.transmission || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {vehicle.fuel_type || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {vehicle.mileage ? `${vehicle.mileage.toLocaleString()} km` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(vehicle.price)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDateShort(vehicle.updated_date)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => openEditForm(vehicle)}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                        title="Edit"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => openDeleteDialog(vehicle)}
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
          Showing {vehicles.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0} to{' '}
          {Math.min(currentPage * itemsPerPage, totalVehicles)} of {totalVehicles} vehicles
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
            disabled={currentPage >= totalPages || vehicles.length < itemsPerPage}
            variant="secondary"
            size="sm"
          >
            Next
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </div>

      {/* Create/Edit Form */}
      <ScrapedVehicleForm
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
        vehicle={selectedVehicle}
        mode={formMode}
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        onConfirm={handleDelete}
        title="Delete Vehicle"
        message={`Are you sure you want to delete ${vehicleToDelete?.manufacturer} ${vehicleToDelete?.model} (${vehicleToDelete?.yom})? This action cannot be undone.`}
        confirmText="Delete"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  );
}

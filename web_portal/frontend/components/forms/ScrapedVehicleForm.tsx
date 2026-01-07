import React, { useState, useEffect } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { ScrapedVehicle, ScrapedVehicleCreate, ScrapedVehicleUpdate } from '@/types';

interface ScrapedVehicleFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ScrapedVehicleCreate | ScrapedVehicleUpdate) => Promise<void>;
  vehicle?: ScrapedVehicle;
  mode: 'create' | 'edit';
}

export const ScrapedVehicleForm: React.FC<ScrapedVehicleFormProps> = ({
  isOpen,
  onClose,
  onSubmit,
  vehicle,
  mode,
}) => {
  const [formData, setFormData] = useState({
    type: '',
    manufacturer: '',
    model: '',
    yom: new Date().getFullYear(),
    transmission: '',
    fuel_type: '',
    mileage: '',
    price: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (vehicle && mode === 'edit') {
      setFormData({
        type: vehicle.type || '',
        manufacturer: vehicle.manufacturer,
        model: vehicle.model,
        yom: vehicle.yom,
        transmission: vehicle.transmission || '',
        fuel_type: vehicle.fuel_type || '',
        mileage: vehicle.mileage?.toString() || '',
        price: vehicle.price?.toString() || '',
      });
    } else {
      setFormData({
        type: '',
        manufacturer: '',
        model: '',
        yom: new Date().getFullYear(),
        transmission: '',
        fuel_type: '',
        mileage: '',
        price: '',
      });
    }
    setError('');
  }, [vehicle, mode, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.type || !formData.manufacturer || !formData.model || !formData.yom) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setIsSubmitting(true);
      const submitData: any = {
        type: formData.type,
        manufacturer: formData.manufacturer,
        model: formData.model,
        yom: formData.yom,
        transmission: formData.transmission || null,
        fuel_type: formData.fuel_type || null,
        mileage: formData.mileage ? parseInt(formData.mileage) : null,
        price: formData.price ? parseFloat(formData.price) : null,
      };

      await onSubmit(submitData);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to save vehicle');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={mode === 'create' ? 'Add Scraped Vehicle' : 'Edit Scraped Vehicle'} size="lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Type <span className="text-red-500">*</span>
          </label>
          <select
            value={formData.type}
            onChange={(e) => setFormData({ ...formData, type: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          >
            <option value="">Select Type</option>
            <option value="REGISTERED">Registered</option>
            <option value="UNREGISTERED">Unregistered</option>
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Manufacturer <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.manufacturer}
              onChange={(e) => setFormData({ ...formData, manufacturer: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., Toyota"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Model <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.model}
              onChange={(e) => setFormData({ ...formData, model: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., Prius"
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Year of Manufacture <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              value={formData.yom}
              onChange={(e) => setFormData({ ...formData, yom: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              min="1900"
              max="2100"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Transmission</label>
            <select
              value={formData.transmission}
              onChange={(e) => setFormData({ ...formData, transmission: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Select</option>
              <option value="Automatic">Automatic</option>
              <option value="Manual">Manual</option>
              <option value="CVT">CVT</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Fuel Type</label>
            <select
              value={formData.fuel_type}
              onChange={(e) => setFormData({ ...formData, fuel_type: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Select</option>
              <option value="Petrol">Petrol</option>
              <option value="Diesel">Diesel</option>
              <option value="Hybrid">Hybrid</option>
              <option value="Electric">Electric</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Mileage (km)</label>
            <input
              type="number"
              value={formData.mileage}
              onChange={(e) => setFormData({ ...formData, mileage: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., 50000"
              min="0"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Price (LKR)</label>
          <input
            type="number"
            value={formData.price}
            onChange={(e) => setFormData({ ...formData, price: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="e.g., 5000000"
            step="0.01"
          />
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <Button type="button" variant="ghost" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="submit" isLoading={isSubmitting}>
            {mode === 'create' ? 'Add Vehicle' : 'Save Changes'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

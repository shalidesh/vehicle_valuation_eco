import React, { useState, useEffect } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { FastMovingVehicle, FastMovingVehicleCreate, FastMovingVehicleUpdate } from '@/types';

interface FastMovingVehicleFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: FastMovingVehicleCreate | FastMovingVehicleUpdate) => Promise<void>;
  vehicle?: FastMovingVehicle;
  mode: 'create' | 'edit';
}

export const FastMovingVehicleForm: React.FC<FastMovingVehicleFormProps> = ({
  isOpen,
  onClose,
  onSubmit,
  vehicle,
  mode,
}) => {
  const [formData, setFormData] = useState({
    type: 'Registered',
    manufacturer: '',
    model: '',
    yom: new Date().getFullYear(),
    price: '',
    date: new Date().toISOString().split('T')[0], // Today's date in YYYY-MM-DD format
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (vehicle && mode === 'edit') {
      setFormData({
        type: vehicle.type,
        manufacturer: vehicle.manufacturer,
        model: vehicle.model,
        yom: vehicle.yom,
        price: vehicle.price?.toString() || '',
        date: vehicle.date ? new Date(vehicle.date).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
      });
    } else {
      setFormData({
        type: 'Registered',
        manufacturer: '',
        model: '',
        yom: new Date().getFullYear(),
        price: '',
        date: new Date().toISOString().split('T')[0],
      });
    }
    setError('');
  }, [vehicle, mode, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.type || !formData.manufacturer || !formData.model || !formData.yom || !formData.date) {
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
        price: formData.price ? parseFloat(formData.price) : null,
        date: new Date(formData.date).toISOString(), // Convert to ISO format for backend
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
    <Modal isOpen={isOpen} onClose={onClose} title={mode === 'create' ? 'Add Vehicle' : 'Edit Vehicle'}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Vehicle Type <span className="text-red-500">*</span>
          </label>
          <select
            value={formData.type}
            onChange={(e) => setFormData({ ...formData, type: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          >
            <option value="Registered">Registered</option>
            <option value="Unregistered">Unregistered</option>
          </select>
        </div>

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
            placeholder="e.g., Corolla"
            required
          />
        </div>

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

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Price Date <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            value={formData.date}
            onChange={(e) => setFormData({ ...formData, date: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Select the date when this price was recorded
          </p>
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

import React, { useState, useEffect } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { SummaryStatistic, SummaryStatisticCreate, SummaryStatisticUpdate } from '@/types';

interface SummaryStatisticFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: SummaryStatisticCreate | SummaryStatisticUpdate) => Promise<void>;
  record?: SummaryStatistic;
  mode: 'create' | 'edit';
}

export const SummaryStatisticForm: React.FC<SummaryStatisticFormProps> = ({
  isOpen,
  onClose,
  onSubmit,
  record,
  mode,
}) => {
  const [formData, setFormData] = useState({
    make: '',
    model: '',
    yom: '',
    transmission: '',
    fuel_type: '',
    average_price: '',
    updated_date: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (record && mode === 'edit') {
      setFormData({
        make: record.make || '',
        model: record.model || '',
        yom: record.yom || '',
        transmission: record.transmission || '',
        fuel_type: record.fuel_type || '',
        average_price: record.average_price?.toString() || '',
        updated_date: record.updated_date || '',
      });
    } else {
      setFormData({
        make: '',
        model: '',
        yom: '',
        transmission: '',
        fuel_type: '',
        average_price: '',
        updated_date: '',
      });
    }
    setError('');
  }, [record, mode, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (mode === 'create') {
      if (!formData.make || !formData.model || !formData.yom || !formData.transmission || !formData.fuel_type) {
        setError('Please fill in all required fields');
        return;
      }

      try {
        setIsSubmitting(true);
        const submitData: SummaryStatisticCreate = {
          make: formData.make,
          model: formData.model,
          yom: formData.yom,
          transmission: formData.transmission,
          fuel_type: formData.fuel_type,
          average_price: formData.average_price ? parseFloat(formData.average_price) : null,
          updated_date: formData.updated_date || null,
        };
        await onSubmit(submitData);
        onClose();
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || 'Failed to save record');
      } finally {
        setIsSubmitting(false);
      }
    } else {
      try {
        setIsSubmitting(true);
        const submitData: SummaryStatisticUpdate = {
          average_price: formData.average_price ? parseFloat(formData.average_price) : null,
          updated_date: formData.updated_date || null,
        };
        await onSubmit(submitData);
        onClose();
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || 'Failed to save record');
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={mode === 'create' ? 'Add Summary Statistic' : 'Edit Summary Statistic'} size="lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        {mode === 'create' ? (
          <>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Make <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.make}
                  onChange={(e) => setFormData({ ...formData, make: e.target.value })}
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

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  YOM <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.yom}
                  onChange={(e) => setFormData({ ...formData, yom: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., 2020"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Transmission <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.transmission}
                  onChange={(e) => setFormData({ ...formData, transmission: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="">Select</option>
                  <option value="Automatic">Automatic</option>
                  <option value="Manual">Manual</option>
                  <option value="CVT">CVT</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Fuel Type <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.fuel_type}
                  onChange={(e) => setFormData({ ...formData, fuel_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="">Select</option>
                  <option value="Petrol">Petrol</option>
                  <option value="Diesel">Diesel</option>
                  <option value="Hybrid">Hybrid</option>
                  <option value="Electric">Electric</option>
                </select>
              </div>
            </div>
          </>
        ) : (
          <div className="bg-gray-50 border border-gray-200 px-4 py-3 rounded-lg text-sm text-gray-700">
            <p><strong>Make:</strong> {record?.make} | <strong>Model:</strong> {record?.model} | <strong>YOM:</strong> {record?.yom}</p>
            <p><strong>Transmission:</strong> {record?.transmission} | <strong>Fuel Type:</strong> {record?.fuel_type}</p>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Average Price (LKR)</label>
            <input
              type="number"
              value={formData.average_price}
              onChange={(e) => setFormData({ ...formData, average_price: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., 5000000"
              step="0.01"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Updated Date</label>
            <input
              type="text"
              value={formData.updated_date}
              onChange={(e) => setFormData({ ...formData, updated_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="e.g., 2026-01-15"
            />
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <Button type="button" variant="ghost" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="submit" isLoading={isSubmitting}>
            {mode === 'create' ? 'Add Record' : 'Save Changes'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

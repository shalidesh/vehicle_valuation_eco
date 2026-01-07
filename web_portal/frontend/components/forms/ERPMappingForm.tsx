import React, { useState, useEffect } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { ERPModelMapping, ERPModelMappingCreate, ERPModelMappingUpdate } from '@/types';

interface ERPMappingFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ERPModelMappingCreate | ERPModelMappingUpdate) => Promise<void>;
  mapping?: ERPModelMapping;
  mode: 'create' | 'edit';
}

export const ERPMappingForm: React.FC<ERPMappingFormProps> = ({
  isOpen,
  onClose,
  onSubmit,
  mapping,
  mode,
}) => {
  const [formData, setFormData] = useState({
    manufacturer: '',
    erp_name: '',
    mapped_name: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (mapping && mode === 'edit') {
      setFormData({
        manufacturer: mapping.manufacturer,
        erp_name: mapping.erp_name,
        mapped_name: mapping.mapped_name,
      });
    } else {
      setFormData({
        manufacturer: '',
        erp_name: '',
        mapped_name: '',
      });
    }
    setError('');
  }, [mapping, mode, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.manufacturer || !formData.erp_name || !formData.mapped_name) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setIsSubmitting(true);
      await onSubmit(formData);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to save mapping');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={mode === 'create' ? 'Add ERP Mapping' : 'Edit ERP Mapping'}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

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
            ERP Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.erp_name}
            onChange={(e) => setFormData({ ...formData, erp_name: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="e.g., CRL"
            required
          />
          <p className="text-xs text-gray-500 mt-1">The model name as it appears in the ERP system</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Mapped Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.mapped_name}
            onChange={(e) => setFormData({ ...formData, mapped_name: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="e.g., Corolla"
            required
          />
          <p className="text-xs text-gray-500 mt-1">The standard model name to map to</p>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <Button type="button" variant="ghost" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="submit" isLoading={isSubmitting}>
            {mode === 'create' ? 'Add Mapping' : 'Save Changes'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

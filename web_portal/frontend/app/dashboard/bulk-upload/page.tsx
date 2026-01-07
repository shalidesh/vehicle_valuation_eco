'use client';

import React, { useState } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/hooks/useAuth';
import { bulkUploadAPI } from '@/lib/api';

interface TableSchema {
  tableName: string;
  displayName: string;
  columns: string[];
  requiredColumns: string[];
}

const TABLE_SCHEMAS: TableSchema[] = [
  {
    tableName: 'fast_moving_vehicles',
    displayName: 'Fast Moving Vehicles',
    columns: ['type', 'manufacturer', 'model', 'yom', 'price', 'date'],
    requiredColumns: ['type', 'manufacturer', 'model', 'yom'],
  },
  {
    tableName: 'scraped_vehicles',
    displayName: 'Scraped Vehicles',
    columns: ['type', 'manufacturer', 'model', 'yom', 'transmission', 'fuel_type', 'mileage', 'price'],
    requiredColumns: ['type', 'manufacturer', 'model', 'yom'],
  },
  {
    tableName: 'erp_model_mappings',
    displayName: 'ERP Model Mappings',
    columns: ['manufacturer', 'erp_name', 'mapped_name'],
    requiredColumns: ['manufacturer', 'erp_name', 'mapped_name'],
  },
];

interface ValidationError {
  row: number;
  column: string;
  message: string;
}

interface UploadResult {
  success: boolean;
  message: string;
  inserted: number;
  duplicates: number;
  errors: ValidationError[];
}

export default function BulkUploadPage() {
  const { user } = useAuth();
  const [selectedTable, setSelectedTable] = useState<TableSchema | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [csvData, setCsvData] = useState<any[]>([]);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [isValidating, setIsValidating] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);

  // Check if user is admin
  if (user?.role !== 'admin') {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600">Only administrators can access bulk upload.</p>
        </div>
      </div>
    );
  }

  const handleTableSelect = (tableName: string) => {
    const schema = TABLE_SCHEMAS.find((t) => t.tableName === tableName);
    setSelectedTable(schema || null);
    setFile(null);
    setCsvData([]);
    setValidationErrors([]);
    setUploadResult(null);
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    if (!selectedFile.name.endsWith('.csv')) {
      alert('Please select a CSV file');
      return;
    }

    setFile(selectedFile);
    setUploadResult(null);
    await parseAndValidateCSV(selectedFile);
  };

  const parseAndValidateCSV = async (file: File) => {
    if (!selectedTable) return;

    setIsValidating(true);
    setValidationErrors([]);

    try {
      const text = await file.text();
      const lines = text.split('\n').filter((line) => line.trim());

      if (lines.length === 0) {
        setValidationErrors([{ row: 0, column: '', message: 'CSV file is empty' }]);
        setIsValidating(false);
        return;
      }

      // Parse header
      const header = lines[0].split(',').map((col) => col.trim().toLowerCase());
      const errors: ValidationError[] = [];

      // Validate header columns
      const missingColumns = selectedTable.requiredColumns.filter(
        (col) => !header.includes(col.toLowerCase())
      );

      if (missingColumns.length > 0) {
        errors.push({
          row: 0,
          column: missingColumns.join(', '),
          message: `Missing required columns: ${missingColumns.join(', ')}`,
        });
      }

      // Check for extra columns
      const extraColumns = header.filter(
        (col) => !selectedTable.columns.map((c) => c.toLowerCase()).includes(col)
      );

      if (extraColumns.length > 0) {
        errors.push({
          row: 0,
          column: extraColumns.join(', '),
          message: `Unknown columns: ${extraColumns.join(', ')}. These will be ignored.`,
        });
      }

      // Parse data rows
      const data: any[] = [];
      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map((val) => val.trim());

        const row: any = {};
        header.forEach((col, index) => {
          if (selectedTable.columns.map((c) => c.toLowerCase()).includes(col)) {
            let value = values[index] || '';

            // Convert text values to uppercase
            if (value && isNaN(Number(value))) {
              value = value.toUpperCase();
            }

            row[col] = value;
          }
        });

        // Validate required fields
        selectedTable.requiredColumns.forEach((reqCol) => {
          if (!row[reqCol.toLowerCase()] || row[reqCol.toLowerCase()] === '') {
            errors.push({
              row: i,
              column: reqCol,
              message: `Missing required value for ${reqCol}`,
            });
          }
        });

        data.push(row);
      }

      setCsvData(data);
      setValidationErrors(errors);
    } catch (error: any) {
      setValidationErrors([
        {
          row: 0,
          column: '',
          message: `Error parsing CSV: ${error.message}`,
        },
      ]);
    } finally {
      setIsValidating(false);
    }
  };

  const handleUpload = async () => {
    if (!selectedTable || !file || csvData.length === 0) return;

    // Block upload if there are ANY validation errors
    if (validationErrors.length > 0) {
      alert('Please fix all validation errors before uploading. No records will be inserted until all errors are resolved.');
      return;
    }

    setIsUploading(true);
    setUploadResult(null);

    try {
      const response = await bulkUploadAPI.uploadCSV(selectedTable.tableName, csvData);
      setUploadResult(response.data);
    } catch (error: any) {
      setUploadResult({
        success: false,
        message: error.response?.data?.detail || 'Upload failed',
        inserted: 0,
        duplicates: 0,
        errors: [],
      });
    } finally {
      setIsUploading(false);
    }
  };

  const hasAnyErrors = validationErrors.length > 0;

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Bulk Data Upload</h1>
        <p className="text-gray-600">
          Upload CSV files to insert bulk records into database tables
        </p>
      </div>

      {/* Step 1: Select Table */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm">
            1
          </span>
          Select Table
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {TABLE_SCHEMAS.map((schema) => (
            <button
              key={schema.tableName}
              onClick={() => handleTableSelect(schema.tableName)}
              className={cn(
                'p-4 border-2 rounded-lg text-left transition-all',
                selectedTable?.tableName === schema.tableName
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-300 hover:border-blue-400'
              )}
            >
              <h3 className="font-semibold text-gray-900 mb-2">{schema.displayName}</h3>
              <p className="text-sm text-gray-600">
                {schema.columns.length} columns
              </p>
            </button>
          ))}
        </div>

        {selectedTable && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-2">Expected CSV Columns:</h3>
            <div className="flex flex-wrap gap-2">
              {selectedTable.columns.map((col) => (
                <span
                  key={col}
                  className={cn(
                    'px-3 py-1 rounded text-sm',
                    selectedTable.requiredColumns.includes(col)
                      ? 'bg-red-100 text-red-800'
                      : 'bg-gray-200 text-gray-700'
                  )}
                >
                  {col}
                  {selectedTable.requiredColumns.includes(col) && ' *'}
                </span>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-2">* Required columns</p>
          </div>
        )}
      </div>

      {/* Step 2: Upload File */}
      {selectedTable && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm">
              2
            </span>
            Upload CSV File
          </h2>

          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <label className="cursor-pointer">
              <span className="text-blue-600 hover:text-blue-700 font-semibold">
                Choose a CSV file
              </span>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>

            {file && (
              <div className="mt-4 flex items-center justify-center gap-2 text-gray-700">
                <FileText className="h-5 w-5" />
                <span className="font-medium">{file.name}</span>
                <span className="text-gray-500">
                  ({(file.size / 1024).toFixed(2)} KB)
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Step 3: Validation Results */}
      {isValidating && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-center gap-3 text-gray-600">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span>Validating CSV file...</span>
          </div>
        </div>
      )}

      {!isValidating && csvData.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm">
              3
            </span>
            Validation Results
          </h2>

          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Total Records</p>
              <p className="text-2xl font-bold text-blue-600">{csvData.length}</p>
            </div>
            <div
              className={cn(
                'p-4 rounded-lg',
                validationErrors.length === 0 ? 'bg-green-50' : 'bg-yellow-50'
              )}
            >
              <p className="text-sm text-gray-600">Validation Issues</p>
              <p
                className={cn(
                  'text-2xl font-bold',
                  validationErrors.length === 0 ? 'text-green-600' : 'text-yellow-600'
                )}
              >
                {validationErrors.length}
              </p>
            </div>
            <div
              className={cn(
                'p-4 rounded-lg',
                hasAnyErrors ? 'bg-red-50' : 'bg-green-50'
              )}
            >
              <p className="text-sm text-gray-600">Status</p>
              <p
                className={cn(
                  'text-lg font-bold',
                  hasAnyErrors ? 'text-red-600' : 'text-green-600'
                )}
              >
                {hasAnyErrors ? 'Has Errors' : 'Ready to Upload'}
              </p>
            </div>
          </div>

          {/* Validation Errors */}
          {validationErrors.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-yellow-600" />
                Validation Issues
              </h3>
              <div className="max-h-60 overflow-y-auto border border-gray-200 rounded-lg">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">
                        Row
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">
                        Column
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">
                        Message
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {validationErrors.map((err, idx) => (
                      <tr key={idx}>
                        <td className="px-4 py-2 text-sm text-gray-900">{err.row}</td>
                        <td className="px-4 py-2 text-sm text-gray-900">{err.column}</td>
                        <td className="px-4 py-2 text-sm text-gray-600">{err.message}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Data Preview */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Data Preview (First 5 rows)</h3>
            <div className="overflow-x-auto border border-gray-200 rounded-lg">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {selectedTable?.columns.map((col) => (
                      <th
                        key={col}
                        className="px-4 py-2 text-left text-xs font-medium text-gray-500"
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {csvData.slice(0, 5).map((row, idx) => (
                    <tr key={idx}>
                      {selectedTable?.columns.map((col) => (
                        <td key={col} className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                          {row[col.toLowerCase()] || '-'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Upload Button */}
          <div className="mt-6 flex justify-end">
            <Button
              onClick={handleUpload}
              disabled={hasAnyErrors || isUploading}
              className="px-6"
            >
              {isUploading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Upload Data
                </>
              )}
            </Button>
          </div>
        </div>
      )}

      {/* Upload Result */}
      {uploadResult && (
        <div
          className={cn(
            'bg-white rounded-lg shadow-md p-6',
            uploadResult.success ? 'border-l-4 border-green-500' : 'border-l-4 border-red-500'
          )}
        >
          <div className="flex items-start gap-3">
            {uploadResult.success ? (
              <CheckCircle className="h-6 w-6 text-green-500 flex-shrink-0 mt-1" />
            ) : (
              <XCircle className="h-6 w-6 text-red-500 flex-shrink-0 mt-1" />
            )}
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 mb-2">
                {uploadResult.success ? 'Upload Successful' : 'Upload Failed'}
              </h3>
              <p className="text-gray-600 mb-4">{uploadResult.message}</p>

              {uploadResult.success && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-green-50 p-3 rounded">
                    <p className="text-sm text-gray-600">Records Inserted</p>
                    <p className="text-xl font-bold text-green-600">{uploadResult.inserted}</p>
                  </div>
                  <div className="bg-yellow-50 p-3 rounded">
                    <p className="text-sm text-gray-600">Duplicates Skipped</p>
                    <p className="text-xl font-bold text-yellow-600">{uploadResult.duplicates}</p>
                  </div>
                </div>
              )}

              {uploadResult.errors && uploadResult.errors.length > 0 && (
                <div className="mt-4">
                  <h4 className="font-semibold text-gray-900 mb-2">Errors:</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {uploadResult.errors.map((err, idx) => (
                      <li key={idx} className="text-sm text-red-600">
                        Row {err.row}, {err.column}: {err.message}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

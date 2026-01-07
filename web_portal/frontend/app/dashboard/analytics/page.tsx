'use client';

import { useEffect, useState, useRef } from 'react';
import { analyticsAPI } from '@/lib/api';
import { PriceMovement, ModelYearOption } from '@/types';
import { Button } from '@/components/ui/Button';
import { TrendingUp, TrendingDown, Minus, X } from 'lucide-react';
import { formatCurrency, handleError } from '@/lib/utils';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  Plugin,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

// Interface for selected points
interface SelectedPoint {
  index: number;
  date: string;
  price: number;
  x: number;
  y: number;
}

export default function AnalyticsPage() {
  const [manufacturers, setManufacturers] = useState<string[]>([]);
  const [models, setModels] = useState<string[]>([]);
  const [years, setYears] = useState<number[]>([]);
  const [availableModelYears, setAvailableModelYears] = useState<ModelYearOption[]>([]);
  const [selectedIndexModels, setSelectedIndexModels] = useState<ModelYearOption[]>([]);

  const [selectedDataSource, setSelectedDataSource] = useState('fast_moving');
  const [selectedVehicleType, setSelectedVehicleType] = useState('');
  const [selectedManufacturer, setSelectedManufacturer] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [selectedDays, setSelectedDays] = useState(90);

  const [priceData, setPriceData] = useState<PriceMovement | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingFilters, setIsLoadingFilters] = useState(true);

  // State for interactive point selection
  const [selectedPoints, setSelectedPoints] = useState<SelectedPoint[]>([]);
  const chartRef = useRef<ChartJS<'line'>>(null);

  useEffect(() => {
    fetchManufacturers();
  }, [selectedDataSource, selectedVehicleType]);

  useEffect(() => {
    if (selectedManufacturer) {
      fetchModels(selectedManufacturer);
    } else {
      setModels([]);
      setSelectedModel('');
    }
  }, [selectedManufacturer, selectedDataSource, selectedVehicleType]);

  useEffect(() => {
    if (selectedManufacturer && selectedModel) {
      fetchYears(selectedManufacturer, selectedModel);
    } else {
      setYears([]);
      setSelectedYear(null);
    }
  }, [selectedManufacturer, selectedModel, selectedDataSource, selectedVehicleType]);

  // Fetch all model-year combinations when Fast Moving Index is selected
  useEffect(() => {
    if (selectedManufacturer === 'Fast Moving Vehicle Index') {
      fetchAllModelYears();
    } else {
      setAvailableModelYears([]);
      setSelectedIndexModels([]);
    }
  }, [selectedManufacturer, selectedDataSource, selectedVehicleType]);

  const fetchManufacturers = async () => {
    try {
      const data = await analyticsAPI.getManufacturers(selectedDataSource, selectedVehicleType || undefined);
      setManufacturers(data);
    } catch (error) {
      console.error('Failed to fetch manufacturers:', error);
    } finally {
      setIsLoadingFilters(false);
    }
  };

  const fetchModels = async (manufacturer: string) => {
    try {
      const data = await analyticsAPI.getModels(manufacturer, selectedDataSource, selectedVehicleType || undefined);
      setModels(data);
    } catch (error) {
      console.error('Failed to fetch models:', error);
    }
  };

  const fetchYears = async (manufacturer: string, model: string) => {
    try {
      const data = await analyticsAPI.getYears(manufacturer, model, selectedDataSource, selectedVehicleType || undefined);
      setYears(data);
    } catch (error) {
      console.error('Failed to fetch years:', error);
    }
  };

  const fetchAllModelYears = async () => {
    try {
      const data = await analyticsAPI.getAllModelYears(selectedDataSource, selectedVehicleType || undefined);
      setAvailableModelYears(data);
      // Set default selections to the hardcoded index components
      const defaultModels = data.filter((item: ModelYearOption) =>
        (item.model.toLowerCase().includes('wagon r') && item.year === 2017) ||
        (item.model.toLowerCase().includes('vezel') && item.year === 2017) ||
        (item.model.toLowerCase().includes('premio') && item.year === 2018) ||
        (item.model.toLowerCase().includes('aqua') && item.year === 2015) ||
        (item.model.toLowerCase().includes('axio') && item.year === 2018)
      );
      setSelectedIndexModels(defaultModels);
    } catch (error) {
      console.error('Failed to fetch model-year combinations:', error);
    }
  };

  const fetchPriceMovement = async () => {
    // Check if Fast Moving Vehicle Index is selected
    const isIndex = selectedManufacturer === 'Fast Moving Vehicle Index';

    if (isIndex && selectedIndexModels.length === 0) {
      alert('Please select at least one model for the index calculation');
      return;
    }

    if (!isIndex && (!selectedManufacturer || !selectedModel || !selectedYear)) {
      alert('Please select manufacturer, model, and year');
      return;
    }

    try {
      setIsLoading(true);
      setSelectedPoints([]); // Clear selected points when fetching new data

      let data;
      if (isIndex) {
        // Fetch index data with selected models
        data = await analyticsAPI.getFastMovingIndex(
          selectedDays,
          selectedDataSource,
          selectedVehicleType || undefined,
          selectedIndexModels
        );
      } else {
        // Fetch regular vehicle data
        data = await analyticsAPI.getPriceMovement(
          selectedManufacturer,
          selectedModel,
          selectedYear!,
          selectedDays,
          selectedDataSource,
          selectedVehicleType || undefined
        );
      }

      setPriceData(data);
    } catch (error) {
      console.error('Failed to fetch price movement:', error);
      alert(handleError(error));
    } finally {
      setIsLoading(false);
    }
  };

  const getTrendIcon = (trend: string | null) => {
    switch (trend) {
      case 'increasing':
        return <TrendingUp className="h-5 w-5 text-green-600" />;
      case 'decreasing':
        return <TrendingDown className="h-5 w-5 text-red-600" />;
      default:
        return <Minus className="h-5 w-5 text-gray-600" />;
    }
  };

  const getTrendColor = (trend: string | null) => {
    switch (trend) {
      case 'increasing':
        return 'text-green-600';
      case 'decreasing':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  // Calculate percentage change between two points
  const calculatePercentageChange = (point1: SelectedPoint, point2: SelectedPoint): number => {
    const startPrice = point1.index < point2.index ? point1.price : point2.price;
    const endPrice = point1.index < point2.index ? point2.price : point1.price;
    return ((endPrice - startPrice) / startPrice) * 100;
  };

  // Handle point click on chart
  const handlePointClick = (event: any, elements: any[]) => {
    if (elements.length === 0 || !priceData) return;

    const clickedIndex = elements[0].index;
    const chart = chartRef.current;
    if (!chart) return;

    const meta = chart.getDatasetMeta(0);
    const point = meta.data[clickedIndex];
    const pricePoint = priceData.price_history[clickedIndex];

    const newPoint: SelectedPoint = {
      index: clickedIndex,
      date: pricePoint.date,
      price: pricePoint.price,
      x: point.x,
      y: point.y,
    };

    setSelectedPoints((prev) => {
      // If we already have 2 points, start over with the new point
      if (prev.length >= 2) {
        return [newPoint];
      }
      // Add the new point
      return [...prev, newPoint];
    });
  };

  // Clear selected points
  const clearSelection = () => {
    setSelectedPoints([]);
  };

  // Custom plugin to draw line between selected points
  const comparisonLinePlugin: Plugin<'line'> = {
    id: 'comparisonLine',
    afterDatasetsDraw(chart) {
      if (selectedPoints.length === 0) return;

      const ctx = chart.ctx;
      const chartArea = chart.chartArea;

      ctx.save();

      // Draw line between points if we have 2 selected
      if (selectedPoints.length === 2) {
        const [point1, point2] = selectedPoints;
        const startPoint = point1.index < point2.index ? point1 : point2;
        const endPoint = point1.index < point2.index ? point2 : point1;

        ctx.beginPath();
        ctx.strokeStyle = 'rgba(99, 102, 241, 0.6)'; // Indigo line
        ctx.lineWidth = 3;
        ctx.setLineDash([8, 4]);
        ctx.moveTo(startPoint.x, startPoint.y);
        ctx.lineTo(endPoint.x, endPoint.y);
        ctx.stroke();
        ctx.setLineDash([]);

        // Draw percentage change label in the middle of the line
        const midX = (startPoint.x + endPoint.x) / 2;
        const midY = (startPoint.y + endPoint.y) / 2;
        const percentChange = calculatePercentageChange(startPoint, endPoint);

        // Background box for percentage
        const percentText = `${percentChange >= 0 ? '+' : ''}${percentChange.toFixed(2)}%`;
        ctx.font = 'bold 14px Arial';
        const textMetrics = ctx.measureText(percentText);
        const boxWidth = textMetrics.width + 20;
        const boxHeight = 28;

        ctx.fillStyle = percentChange >= 0 ? 'rgba(34, 197, 94, 0.95)' : 'rgba(239, 68, 68, 0.95)';
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.roundRect(midX - boxWidth / 2, midY - boxHeight / 2, boxWidth, boxHeight, 6);
        ctx.fill();
        ctx.stroke();

        // Percentage text
        ctx.fillStyle = 'white';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(percentText, midX, midY);
      }

      // Draw circles at selected points with different colors
      selectedPoints.forEach((point, index) => {
        // Determine if this is start or end point
        const isStartPoint = selectedPoints.length === 2
          ? (selectedPoints[0].index < selectedPoints[1].index
              ? index === 0
              : index === 1)
          : true;

        // Color coding: Green for start, Red for end, Blue for single point
        let fillColor, strokeColor, labelColor, label;
        if (selectedPoints.length === 1) {
          fillColor = 'rgba(59, 130, 246, 1)'; // Blue
          strokeColor = 'rgba(30, 64, 175, 1)';
          labelColor = 'white';
          label = '1';
        } else {
          if (isStartPoint) {
            fillColor = 'rgba(34, 197, 94, 1)'; // Green
            strokeColor = 'rgba(21, 128, 61, 1)';
            labelColor = 'white';
            label = 'S';
          } else {
            fillColor = 'rgba(239, 68, 68, 1)'; // Red
            strokeColor = 'rgba(185, 28, 28, 1)';
            labelColor = 'white';
            label = 'E';
          }
        }

        // Draw outer glow
        ctx.beginPath();
        ctx.arc(point.x, point.y, 12, 0, 2 * Math.PI);
        ctx.fillStyle = fillColor.replace('1)', '0.2)');
        ctx.fill();

        // Draw main circle
        ctx.beginPath();
        ctx.arc(point.x, point.y, 8, 0, 2 * Math.PI);
        ctx.fillStyle = fillColor;
        ctx.fill();
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 3;
        ctx.stroke();

        // Draw white border
        ctx.beginPath();
        ctx.arc(point.x, point.y, 8, 0, 2 * Math.PI);
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Draw label (S for Start, E for End, or number)
        ctx.fillStyle = labelColor;
        ctx.font = 'bold 10px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(label, point.x, point.y);

        // Draw info box near the point
        const date = new Date(point.date).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        });
        const price = formatCurrency(point.price);

        // Position the info box
        // Determine if point is in left or right half of chart
        const isLeftSide = point.x < (chartArea.left + chartArea.right) / 2;
        const boxPadding = 8;
        const boxOffsetX = isLeftSide ? 25 : -25;
        const boxOffsetY = point.y < chartArea.top + 80 ? 40 : -40; // Below if near top, above otherwise

        // Measure text for box sizing
        ctx.font = 'bold 11px Arial';
        const priceWidth = ctx.measureText(price).width;
        ctx.font = '10px Arial';
        const dateWidth = ctx.measureText(date).width;
        const maxWidth = Math.max(priceWidth, dateWidth);

        const infoBoxWidth = maxWidth + boxPadding * 2;
        const infoBoxHeight = 36;

        let infoBoxX = point.x + boxOffsetX;
        let infoBoxY = point.y + boxOffsetY;

        // Adjust position if box would go outside chart area
        if (isLeftSide && infoBoxX + infoBoxWidth > chartArea.right - 10) {
          infoBoxX = chartArea.right - infoBoxWidth - 10;
        } else if (!isLeftSide && infoBoxX - infoBoxWidth < chartArea.left + 10) {
          infoBoxX = chartArea.left + 10;
        }

        // Draw info box background
        ctx.fillStyle = 'rgba(255, 255, 255, 0.98)';
        ctx.strokeStyle = fillColor;
        ctx.lineWidth = 2;
        ctx.beginPath();
        const cornerX = isLeftSide ? infoBoxX : infoBoxX - infoBoxWidth;
        ctx.roundRect(cornerX, infoBoxY - infoBoxHeight / 2, infoBoxWidth, infoBoxHeight, 6);
        ctx.fill();
        ctx.stroke();

        // Draw connecting line from point to info box
        ctx.beginPath();
        ctx.strokeStyle = fillColor;
        ctx.lineWidth = 1.5;
        ctx.moveTo(point.x, point.y);
        ctx.lineTo(cornerX + (isLeftSide ? 0 : infoBoxWidth), infoBoxY);
        ctx.stroke();

        // Draw date
        ctx.fillStyle = '#4B5563';
        ctx.font = '10px Arial';
        ctx.textAlign = isLeftSide ? 'left' : 'right';
        ctx.textBaseline = 'middle';
        ctx.fillText(
          date,
          isLeftSide ? cornerX + boxPadding : cornerX + infoBoxWidth - boxPadding,
          infoBoxY - 8
        );

        // Draw price
        ctx.fillStyle = fillColor.replace('1)', '1)');
        ctx.font = 'bold 11px Arial';
        ctx.fillText(
          price,
          isLeftSide ? cornerX + boxPadding : cornerX + infoBoxWidth - boxPadding,
          infoBoxY + 8
        );
      });

      ctx.restore();
    },
  };

  const chartData = priceData
    ? {
        labels: priceData.price_history.map((point) =>
          new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
        ),
        datasets: [
          {
            label: priceData.manufacturer === 'Fast Moving Vehicle Index' ? 'Index Value' : 'Price (LKR)',
            data: priceData.price_history.map((point) => point.price),
            borderColor: 'rgb(59, 130, 246)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.3,
            fill: true,
          },
        ],
      }
    : null;

  const chartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    onClick: handlePointClick,
    layout: {
      padding: {
        top: 40,
        right: 40,
        bottom: 20,
        left: 20,
      },
    },
    plugins: {
      legend: {
        display: true,
        position: 'top',
      },
      title: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const label = priceData?.manufacturer === 'Fast Moving Vehicle Index' ? 'Index Value' : 'Price';
            return `${label}: ${formatCurrency(context.parsed.y)}`;
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: false,
        ticks: {
          callback: (value) => formatCurrency(Number(value)),
        },
      },
    },
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Price Analytics</h1>

      {/* Selection Panel */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Vehicle</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
          {/* Data Source */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Data Source
            </label>
            <select
              value={selectedDataSource}
              onChange={(e) => {
                setSelectedDataSource(e.target.value);
                setSelectedManufacturer('');
                setSelectedModel('');
                setSelectedYear(null);
                setPriceData(null);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="fast_moving">Fast Moving Vehicle Data</option>
              <option value="scraped">Scrape Data</option>
            </select>
          </div>

          {/* Vehicle Type (only for fast_moving) */}
          {selectedDataSource === 'fast_moving' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Vehicle Type
              </label>
              <select
                value={selectedVehicleType}
                onChange={(e) => {
                  setSelectedVehicleType(e.target.value);
                  setSelectedManufacturer('');
                  setSelectedModel('');
                  setSelectedYear(null);
                  setPriceData(null);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Types</option>
                <option value="Registered">Registered</option>
                <option value="Unregistered">Unregistered</option>
              </select>
            </div>
          )}

          {/* Manufacturer */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Manufacturer
            </label>
            <select
              value={selectedManufacturer}
              onChange={(e) => {
                setSelectedManufacturer(e.target.value);
                setSelectedModel('');
                setSelectedYear(null);
                setPriceData(null);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoadingFilters}
            >
              <option value="">Select Manufacturer</option>
              {selectedDataSource === 'fast_moving' && (
                <option value="Fast Moving Vehicle Index">Fast Moving Vehicle Index</option>
              )}
              {manufacturers.map((manufacturer) => (
                <option key={manufacturer} value={manufacturer}>
                  {manufacturer}
                </option>
              ))}
            </select>
          </div>

          {/* Multi-select for Index Models - Show only when Fast Moving Index is selected */}
          {selectedManufacturer === 'Fast Moving Vehicle Index' && (
            <div className="md:col-span-2 lg:col-span-3">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Models for Index Calculation ({selectedIndexModels.length} selected)
              </label>
              <div className="border border-gray-300 rounded-lg p-3 max-h-60 overflow-y-auto bg-white">
                {availableModelYears.length === 0 ? (
                  <p className="text-sm text-gray-500">Loading models...</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                    {availableModelYears.map((modelYear) => (
                      <label
                        key={`${modelYear.manufacturer}-${modelYear.model}-${modelYear.year}`}
                        className="flex items-center space-x-2 p-2 rounded hover:bg-gray-50 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={selectedIndexModels.some(
                            (selected) =>
                              selected.manufacturer === modelYear.manufacturer &&
                              selected.model === modelYear.model &&
                              selected.year === modelYear.year
                          )}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedIndexModels([...selectedIndexModels, modelYear]);
                            } else {
                              setSelectedIndexModels(
                                selectedIndexModels.filter(
                                  (selected) =>
                                    !(
                                      selected.manufacturer === modelYear.manufacturer &&
                                      selected.model === modelYear.model &&
                                      selected.year === modelYear.year
                                    )
                                )
                              );
                            }
                          }}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700">{modelYear.label}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
              <div className="mt-2 flex gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedIndexModels(availableModelYears)}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  Select All
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedIndexModels([])}
                  className="text-sm text-red-600 hover:text-red-800"
                >
                  Clear All
                </button>
              </div>
            </div>
          )}

          {/* Model - Hide when index is selected */}
          {selectedManufacturer !== 'Fast Moving Vehicle Index' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Model</label>
              <select
                value={selectedModel}
                onChange={(e) => {
                  setSelectedModel(e.target.value);
                  setSelectedYear(null);
                  setPriceData(null);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={!selectedManufacturer}
              >
                <option value="">Select Model</option>
                {models.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Year - Hide when index is selected */}
          {selectedManufacturer !== 'Fast Moving Vehicle Index' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Year</label>
              <select
                value={selectedYear || ''}
                onChange={(e) => {
                  setSelectedYear(Number(e.target.value));
                  setPriceData(null);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={!selectedModel}
              >
                <option value="">Select Year</option>
                {years.map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Time Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Time Range</label>
            <select
              value={selectedDays}
              onChange={(e) => setSelectedDays(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value={90}>Last 3 months</option>
              <option value={180}>Last 6 months</option>
              <option value={365}>Last 12 months</option>
              <option value={36500}>All time</option>
            </select>
          </div>
        </div>

        <Button
          onClick={fetchPriceMovement}
          disabled={
            !selectedManufacturer ||
            (selectedManufacturer === 'Fast Moving Vehicle Index' && selectedIndexModels.length === 0) ||
            (selectedManufacturer !== 'Fast Moving Vehicle Index' && (!selectedModel || !selectedYear))
          }
          isLoading={isLoading}
        >
          {selectedManufacturer === 'Fast Moving Vehicle Index'
            ? 'Analyze Index Movement'
            : 'Analyze Price Movement'}
        </Button>
      </div>

      {/* Results */}
      {priceData && (
        <>
          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">
                {priceData.manufacturer === 'Fast Moving Vehicle Index' ? 'Average Index' : 'Average Price'}
              </p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(priceData.avg_price)}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">
                {priceData.manufacturer === 'Fast Moving Vehicle Index' ? 'Minimum Index' : 'Minimum Price'}
              </p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(priceData.min_price)}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">
                {priceData.manufacturer === 'Fast Moving Vehicle Index' ? 'Maximum Index' : 'Maximum Price'}
              </p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(priceData.max_price)}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">
                {priceData.manufacturer === 'Fast Moving Vehicle Index' ? 'Index Trend' : 'Price Trend'}
              </p>
              <div className="flex items-center gap-2">
                {getTrendIcon(priceData.trend)}
                <p className={`text-xl font-bold capitalize ${getTrendColor(priceData.trend)}`}>
                  {priceData.trend || 'Stable'}
                </p>
              </div>
            </div>
          </div>

          {/* Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex flex-col gap-3 mb-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">
                  {priceData.manufacturer === 'Fast Moving Vehicle Index'
                    ? 'Fast Moving Vehicle Index Movement'
                    : `Price Movement - ${priceData.manufacturer} ${priceData.model} (${priceData.yom})`
                  }
                </h2>
                <div className="flex items-center gap-3">
                  <p className="text-sm text-gray-600">
                    {selectedPoints.length === 0 && 'Click on two points to compare'}
                    {selectedPoints.length === 1 && 'Select one more point'}
                    {selectedPoints.length === 2 && 'Comparing two points'}
                  </p>
                  {selectedPoints.length > 0 && (
                    <button
                      onClick={clearSelection}
                      className="flex items-center gap-1 px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <X className="h-4 w-4" />
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {/* Legend for point selection */}
              {selectedPoints.length > 0 && (
                <div className="flex items-center gap-4 px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
                  <span className="text-xs font-medium text-gray-600">Legend:</span>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center justify-center w-5 h-5 rounded-full bg-green-500 text-white text-xs font-bold">
                      S
                    </div>
                    <span className="text-xs text-gray-700">Start Point (Earlier Date)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center justify-center w-5 h-5 rounded-full bg-red-500 text-white text-xs font-bold">
                      E
                    </div>
                    <span className="text-xs text-gray-700">End Point (Later Date)</span>
                  </div>
                </div>
              )}
            </div>

            {/* Percentage Change Display */}
            {selectedPoints.length === 2 && (
              <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border-2 border-blue-200">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Start Point */}
                  <div className="bg-white rounded-lg p-3 shadow-sm border-2 border-green-400">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="flex items-center justify-center w-6 h-6 rounded-full bg-green-500 text-white text-xs font-bold shadow-sm">
                        S
                      </div>
                      <p className="text-xs font-medium text-gray-500">Start Point</p>
                    </div>
                    <p className="text-sm text-gray-700">
                      {new Date(
                        selectedPoints[0].index < selectedPoints[1].index
                          ? selectedPoints[0].date
                          : selectedPoints[1].date
                      ).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </p>
                    <p className="text-lg font-bold text-green-700">
                      {formatCurrency(
                        selectedPoints[0].index < selectedPoints[1].index
                          ? selectedPoints[0].price
                          : selectedPoints[1].price
                      )}
                    </p>
                  </div>

                  {/* Percentage Change */}
                  <div className="bg-white rounded-lg p-3 shadow-sm border-2 border-indigo-400">
                    <p className="text-xs font-medium text-gray-500 mb-1">Price Change</p>
                    <p
                      className={`text-2xl font-bold ${
                        calculatePercentageChange(selectedPoints[0], selectedPoints[1]) >= 0
                          ? 'text-green-600'
                          : 'text-red-600'
                      }`}
                    >
                      {calculatePercentageChange(selectedPoints[0], selectedPoints[1]) >= 0
                        ? '+'
                        : ''}
                      {calculatePercentageChange(selectedPoints[0], selectedPoints[1]).toFixed(2)}%
                    </p>
                    <p className="text-xs text-gray-600 mt-1">
                      {formatCurrency(
                        Math.abs(
                          (selectedPoints[0].index < selectedPoints[1].index
                            ? selectedPoints[1].price - selectedPoints[0].price
                            : selectedPoints[0].price - selectedPoints[1].price)
                        )
                      )}{' '}
                      {calculatePercentageChange(selectedPoints[0], selectedPoints[1]) >= 0
                        ? 'increase'
                        : 'decrease'}
                    </p>
                  </div>

                  {/* End Point */}
                  <div className="bg-white rounded-lg p-3 shadow-sm border-2 border-red-400">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="flex items-center justify-center w-6 h-6 rounded-full bg-red-500 text-white text-xs font-bold shadow-sm">
                        E
                      </div>
                      <p className="text-xs font-medium text-gray-500">End Point</p>
                    </div>
                    <p className="text-sm text-gray-700">
                      {new Date(
                        selectedPoints[0].index < selectedPoints[1].index
                          ? selectedPoints[1].date
                          : selectedPoints[0].date
                      ).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </p>
                    <p className="text-lg font-bold text-red-700">
                      {formatCurrency(
                        selectedPoints[0].index < selectedPoints[1].index
                          ? selectedPoints[1].price
                          : selectedPoints[0].price
                      )}
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div style={{ height: '500px', cursor: 'pointer' }}>
              {chartData && (
                <Line
                  ref={chartRef}
                  data={chartData}
                  options={chartOptions}
                  plugins={[comparisonLinePlugin]}
                />
              )}
            </div>
          </div>
        </>
      )}

      {/* Empty State */}
      {!priceData && !isLoading && (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <TrendingUp className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No Price Data Yet
          </h3>
          <p className="text-gray-600">
            Select a vehicle and click "Analyze Price Movement" to view price trends and
            statistics.
          </p>
        </div>
      )}
    </div>
  );
}

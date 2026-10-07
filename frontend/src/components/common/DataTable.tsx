import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';

export interface ColumnDef<T> {
  header: string;
  accessorKey?: keyof T;
  cell?: (row: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  searchKey?: keyof T;
  searchPlaceholder?: string;
  pageSize?: number;
  emptyMessage?: string;
  onRowClick?: (row: T) => void;
}

export function DataTable<T extends Record<string, any>>({
  columns,
  data,
  searchKey,
  searchPlaceholder = 'Filter records...',
  pageSize = 10,
  emptyMessage = 'No matching records found.',
  onRowClick,
}: DataTableProps<T>) {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  const filteredData = React.useMemo(() => {
    if (!searchTerm || !searchKey) return data;
    const lower = searchTerm.toLowerCase();
    return data.filter((item) => {
      const val = item[searchKey];
      return String(val || '').toLowerCase().includes(lower);
    });
  }, [data, searchTerm, searchKey]);

  const totalPages = Math.ceil(filteredData.length / pageSize) || 1;
  const paginatedData = React.useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredData.slice(start, start + pageSize);
  }, [filteredData, currentPage, pageSize]);

  return (
    <div className="w-full bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      {searchKey && (
        <div className="p-3 border-b border-slate-800/80 bg-slate-900/40 flex items-center justify-between">
          <div className="relative w-72">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              placeholder={searchPlaceholder}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-sans"
            />
          </div>
          <div className="text-xs text-slate-500 font-mono">
            Showing {filteredData.length} records
          </div>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-mono tracking-wider">
              {columns.map((col, idx) => (
                <th key={idx} className={`p-3.5 font-semibold ${col.className || ''}`}>
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {paginatedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="p-8 text-center text-slate-500">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paginatedData.map((row, rowIdx) => (
                <tr
                  key={rowIdx}
                  onClick={() => onRowClick && onRowClick(row)}
                  className={`hover:bg-slate-800/40 transition-colors ${
                    onRowClick ? 'cursor-pointer' : ''
                  }`}
                >
                  {columns.map((col, colIdx) => (
                    <td key={colIdx} className={`p-3.5 text-slate-300 ${col.className || ''}`}>
                      {col.cell
                        ? col.cell(row)
                        : col.accessorKey
                        ? String(row[col.accessorKey] ?? '-')
                        : null}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="p-3 border-t border-slate-800/80 bg-slate-950/40 flex items-center justify-between text-xs text-slate-400">
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
              disabled={currentPage === 1}
              className="p-1.5 rounded-lg border border-slate-800 bg-slate-900 disabled:opacity-40 hover:bg-slate-800 disabled:hover:bg-slate-900 transition cursor-pointer"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
              disabled={currentPage === totalPages}
              className="p-1.5 rounded-lg border border-slate-800 bg-slate-900 disabled:opacity-40 hover:bg-slate-800 disabled:hover:bg-slate-900 transition cursor-pointer"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

import type { AgeFilter, SortField } from '../types';
import { FiSearch, FiX } from 'react-icons/fi';

interface Props {
  search: string;
  ageFilter: AgeFilter;
  sunshineOnly: boolean;
  activeFilterCount: number;
  allGenres: string[];
  allDrives: string[];
  selectedGenres: Set<string>;
  selectedDrives: Set<string>;
  selectedEsrb: Set<string>;
  sortField: SortField;
  sortDir: 'asc' | 'desc';
  onSearch: (v: string) => void;
  onAgeFilter: (v: AgeFilter) => void;
  onToggleEsrb: (v: string) => void;
  onToggleGenre: (v: string) => void;
  onToggleDrive: (v: string) => void;
  onToggleSunshine: () => void;
  onSort: (v: SortField) => void;
  onClear: () => void;
}

const ESRB_OPTIONS = ['E', 'E10', 'T', 'M', 'AO', 'Unrated'];
const AGE_OPTIONS: { value: AgeFilter; label: string }[] = [
  { value: 'all', label: 'All Ages' },
  { value: 'family_friendly', label: 'Family (E-T)' },
  { value: 'kid_safe', label: 'Kids (E/E10+)' },
];
const SORT_OPTIONS: { value: SortField; label: string }[] = [
  { value: 'name', label: 'Name' },
  { value: 'metacritic', label: 'Metacritic' },
  { value: 'rating', label: 'Rating' },
  { value: 'released', label: 'Release Date' },
  { value: 'esrb', label: 'Age Rating' },
];

export function FilterBar(props: Props) {
  return (
    <div className="px-4 sm:px-6 pb-4 space-y-3">
      {/* Search */}
      <div className="relative">
        <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          placeholder="Search games, genres, tags..."
          value={props.search}
          onChange={(e) => props.onSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        />
        {props.search && (
          <button
            onClick={() => props.onSearch('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white cursor-pointer"
          >
            <FiX className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Filter pills row */}
      <div className="flex flex-wrap gap-2 items-center">
        {/* Age filter */}
        {AGE_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => props.onAgeFilter(opt.value)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer ${
              props.ageFilter === opt.value
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
          >
            {opt.label}
          </button>
        ))}

        <span className="w-px h-6 bg-gray-700" />

        {/* ESRB pills */}
        {ESRB_OPTIONS.map((rating) => (
          <button
            key={rating}
            onClick={() => props.onToggleEsrb(rating === 'Unrated' ? 'Unrated' : rating)}
            className={`px-2.5 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer ${
              props.selectedEsrb.has(rating === 'Unrated' ? 'Unrated' : rating)
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
          >
            {rating}
          </button>
        ))}

        <span className="w-px h-6 bg-gray-700" />

        {/* Sunshine toggle */}
        <button
          onClick={props.onToggleSunshine}
          className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer ${
            props.sunshineOnly
              ? 'bg-amber-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
          }`}
        >
          Streaming
        </button>

        {/* Clear all */}
        {props.activeFilterCount > 0 && (
          <button
            onClick={props.onClear}
            className="px-3 py-1.5 rounded-full text-xs font-medium bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors cursor-pointer"
          >
            Clear ({props.activeFilterCount})
          </button>
        )}
      </div>

      {/* Sort + Drive + Genre row */}
      <div className="flex flex-wrap gap-2 items-center">
        {/* Sort */}
        <span className="text-xs text-gray-500">Sort:</span>
        {SORT_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => props.onSort(opt.value)}
            className={`px-2.5 py-1 rounded text-xs font-medium transition-colors cursor-pointer ${
              props.sortField === opt.value
                ? 'bg-gray-700 text-white'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            {opt.label}
            {props.sortField === opt.value && (
              <span className="ml-1">{props.sortDir === 'asc' ? '↑' : '↓'}</span>
            )}
          </button>
        ))}

        <span className="w-px h-6 bg-gray-700" />

        {/* Drive filter */}
        <span className="text-xs text-gray-500">Drive:</span>
        {props.allDrives.map((drive) => (
          <button
            key={drive}
            onClick={() => props.onToggleDrive(drive)}
            className={`px-2 py-1 rounded text-xs font-medium transition-colors cursor-pointer ${
              props.selectedDrives.has(drive)
                ? 'bg-indigo-600 text-white'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            {drive}:
          </button>
        ))}

        {/* Genre dropdown */}
        {props.allGenres.length > 0 && (
          <>
            <span className="w-px h-6 bg-gray-700" />
            <div className="relative group">
              <button className="px-3 py-1 rounded text-xs font-medium text-gray-500 hover:text-gray-300 bg-gray-800 cursor-pointer">
                Genres {props.selectedGenres.size > 0 && `(${props.selectedGenres.size})`}
              </button>
              <div className="absolute top-full left-0 pt-1 hidden group-hover:block z-40">
                <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-xl p-2 max-h-64 overflow-y-auto w-48">
                  {props.allGenres.map((genre) => (
                    <button
                      key={genre}
                      onClick={() => props.onToggleGenre(genre)}
                      className={`block w-full text-left px-2 py-1 rounded text-xs transition-colors cursor-pointer ${
                        props.selectedGenres.has(genre)
                          ? 'bg-indigo-600 text-white'
                          : 'text-gray-400 hover:bg-gray-700 hover:text-white'
                      }`}
                    >
                      {genre}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

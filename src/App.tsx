import { useState } from 'react';
import type { Game } from './types';
import { useGames } from './hooks/useGames';
import { Header } from './components/Header';
import { FilterBar } from './components/FilterBar';
import { GameGrid } from './components/GameGrid';
import { GameDetail } from './components/GameDetail';

export default function App() {
  const {
    games,
    totalCount,
    loading,
    error,
    filters,
    allGenres,
    allDrives,
    activeFilterCount,
    setSearch,
    setAgeFilter,
    toggleEsrb,
    toggleGenre,
    toggleDrive,
    toggleSunshine,
    setSort,
    clearFilters,
  } = useGames();

  const [selectedGame, setSelectedGame] = useState<Game | null>(null);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-400">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p>Loading game library...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-400">
        <div className="text-center max-w-md">
          <p className="text-red-400 text-xl mb-2">Failed to load games</p>
          <p className="text-sm">{error}</p>
          <p className="text-sm mt-4">
            Make sure <code className="bg-gray-800 px-1 rounded">public/data/games.json</code> exists.
            Run the scan and fetch scripts first.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950">
      <div className="max-w-7xl mx-auto">
        <Header games={games} totalCount={totalCount} />
        <FilterBar
          search={filters.search}
          ageFilter={filters.ageFilter}
          sunshineOnly={filters.sunshineOnly}
          activeFilterCount={activeFilterCount}
          allGenres={allGenres}
          allDrives={allDrives}
          selectedGenres={filters.genres}
          selectedDrives={filters.drives}
          selectedEsrb={filters.esrbRatings}
          sortField={filters.sortField}
          sortDir={filters.sortDir}
          onSearch={setSearch}
          onAgeFilter={setAgeFilter}
          onToggleEsrb={toggleEsrb}
          onToggleGenre={toggleGenre}
          onToggleDrive={toggleDrive}
          onToggleSunshine={toggleSunshine}
          onSort={setSort}
          onClear={clearFilters}
        />
        <GameGrid
          games={games}
          totalCount={totalCount}
          onSelect={setSelectedGame}
        />
      </div>

      {selectedGame && (
        <GameDetail game={selectedGame} onClose={() => setSelectedGame(null)} />
      )}
    </div>
  );
}

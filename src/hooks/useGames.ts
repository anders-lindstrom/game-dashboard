import { useState, useEffect, useMemo } from 'react';
import type { Game, FilterState, SortField, AgeFilter } from '../types';

const DEFAULT_FILTERS: FilterState = {
  search: '',
  ageFilter: 'all',
  esrbRatings: new Set(),
  genres: new Set(),
  drives: new Set(),
  sunshineOnly: false,
  sortField: 'name',
  sortDir: 'asc',
};

export function useGames() {
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);

  useEffect(() => {
    fetch('/data/games.json')
      .then((r) => {
        if (!r.ok) throw new Error('Failed to load games data');
        return r.json();
      })
      .then((data: Game[]) => {
        setGames(data);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, []);

  const allGenres = useMemo(() => {
    const set = new Set<string>();
    games.forEach((g) => g.genres?.forEach((genre) => set.add(genre)));
    return Array.from(set).sort();
  }, [games]);

  const allDrives = useMemo(() => {
    const set = new Set<string>();
    games.forEach((g) => g.paths?.forEach((p) => set.add(p.drive)));
    return Array.from(set).sort();
  }, [games]);

  const filtered = useMemo(() => {
    let result = games;

    // Text search
    if (filters.search) {
      const q = filters.search.toLowerCase();
      result = result.filter(
        (g) =>
          g.name.toLowerCase().includes(q) ||
          g.genres?.some((genre) => genre.toLowerCase().includes(q)) ||
          g.tags?.some((tag) => tag.toLowerCase().includes(q))
      );
    }

    // Age filter
    if (filters.ageFilter === 'kid_safe') {
      result = result.filter((g) => g.kid_safe === true);
    } else if (filters.ageFilter === 'family_friendly') {
      result = result.filter((g) => g.family_friendly === true);
    }

    // ESRB checkboxes
    if (filters.esrbRatings.size > 0) {
      result = result.filter((g) => {
        const rating = g.esrb_rating || 'Unrated';
        return filters.esrbRatings.has(rating);
      });
    }

    // Genre filter
    if (filters.genres.size > 0) {
      result = result.filter((g) =>
        g.genres?.some((genre) => filters.genres.has(genre))
      );
    }

    // Drive filter
    if (filters.drives.size > 0) {
      result = result.filter((g) =>
        g.paths?.some((p) => filters.drives.has(p.drive))
      );
    }

    // Sunshine only
    if (filters.sunshineOnly) {
      result = result.filter((g) => g.in_sunshine);
    }

    // Sort
    result = [...result].sort((a, b) => {
      const dir = filters.sortDir === 'asc' ? 1 : -1;
      switch (filters.sortField) {
        case 'name':
          return dir * a.name.localeCompare(b.name);
        case 'metacritic':
          return dir * ((a.metacritic ?? -1) - (b.metacritic ?? -1));
        case 'rating':
          return dir * ((a.rawg_rating ?? -1) - (b.rawg_rating ?? -1));
        case 'released':
          return dir * ((a.released ?? '').localeCompare(b.released ?? ''));
        case 'esrb':
          return dir * ((a.min_age ?? 99) - (b.min_age ?? 99));
        default:
          return 0;
      }
    });

    return result;
  }, [games, filters]);

  const setSearch = (search: string) =>
    setFilters((f) => ({ ...f, search }));

  const setAgeFilter = (ageFilter: AgeFilter) =>
    setFilters((f) => ({ ...f, ageFilter }));

  const toggleEsrb = (rating: string) =>
    setFilters((f) => {
      const next = new Set(f.esrbRatings);
      next.has(rating) ? next.delete(rating) : next.add(rating);
      return { ...f, esrbRatings: next };
    });

  const toggleGenre = (genre: string) =>
    setFilters((f) => {
      const next = new Set(f.genres);
      next.has(genre) ? next.delete(genre) : next.add(genre);
      return { ...f, genres: next };
    });

  const toggleDrive = (drive: string) =>
    setFilters((f) => {
      const next = new Set(f.drives);
      next.has(drive) ? next.delete(drive) : next.add(drive);
      return { ...f, drives: next };
    });

  const toggleSunshine = () =>
    setFilters((f) => ({ ...f, sunshineOnly: !f.sunshineOnly }));

  const setSort = (sortField: SortField) =>
    setFilters((f) => ({
      ...f,
      sortField,
      sortDir:
        f.sortField === sortField
          ? f.sortDir === 'asc'
            ? 'desc'
            : 'asc'
          : sortField === 'name'
            ? 'asc'
            : 'desc',
    }));

  const clearFilters = () => setFilters(DEFAULT_FILTERS);

  const activeFilterCount = [
    filters.search !== '',
    filters.ageFilter !== 'all',
    filters.esrbRatings.size > 0,
    filters.genres.size > 0,
    filters.drives.size > 0,
    filters.sunshineOnly,
  ].filter(Boolean).length;

  return {
    games: filtered,
    totalCount: games.length,
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
  };
}

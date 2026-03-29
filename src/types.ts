export interface GamePath {
  drive: string;
  path: string;
}

export interface SourceInfo {
  id: number;
  name: string;
  match_confidence: 'confident' | 'uncertain' | 'none' | 'unknown';
  fetched_at: string;
}

export interface Game {
  id: string;
  name: string;
  folder_name: string;
  paths: GamePath[];
  in_sunshine: boolean;
  // Merged ratings
  metacritic: number | null;
  esrb_rating: string | null;
  min_age: number | null;
  family_friendly: boolean | null;
  kid_safe: boolean | null;
  content_descriptors: string[];
  pegi_age: number | null;
  // Media
  background_image: string | null;
  description: string;
  released: string | null;
  // Taxonomy
  genres: string[];
  platforms: string[];
  tags: string[];
  developers: string[];
  publishers: string[];
  // Per-source ratings
  rawg_rating: number | null;
  rawg_ratings_count: number;
  igdb_rating: number | null;
  igdb_rating_count: number;
  aggregated_rating: number | null;
  // Provenance
  sources: {
    rawg?: SourceInfo;
    igdb?: SourceInfo;
  };
  match_quality: 'confident' | 'uncertain' | 'none';
  merged_at: string;
}

export type SortField = 'name' | 'metacritic' | 'rating' | 'released' | 'esrb';
export type SortDir = 'asc' | 'desc';
export type AgeFilter = 'all' | 'kid_safe' | 'family_friendly';

export interface FilterState {
  search: string;
  ageFilter: AgeFilter;
  esrbRatings: Set<string>;
  genres: Set<string>;
  drives: Set<string>;
  sunshineOnly: boolean;
  sortField: SortField;
  sortDir: SortDir;
}

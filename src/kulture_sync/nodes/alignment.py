import os
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from kulture_sync.state.firestore import StateManager


class SouthAfricanSubgenre(str, Enum):
    AMAPIANO = "Amapiano"
    GQOM = "Gqom"
    LEKOMPO = "Lekompo"
    MOTSWAKO = "Motswako"
    BACARDI = "Bacardi"
    MASKANDI = "Maskandi"


class SubgenreClassificationResponse(BaseModel):
    selected_subgenre: SouthAfricanSubgenre = Field(
        description="The precise South African musical subgenre matching the track."
    )
    confidence_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Model classification confidence score between 0.0 and 1.0"
    )


class CulturalAlignmentNode:
    def __init__(self, state_manager: StateManager):
        self.state_mgr = state_manager
        self.has_gemini = "GEMINI_API_KEY" in os.environ or "GOOGLE_APPLICATION_CREDENTIALS" in os.environ

    def execute(self, track_chunk: List[Dict[str, Any]], chunk_idx: int) -> Dict[str, Any]:
        """
        Executes cultural alignment on a chunk of tracks with strict write idempotency.
        Tracks are deduplicated by track_id inside playlists to ensure duplicate executions
        yield identical, deterministic state.
        """
        print(f"[CulturalAlignmentNode] Aligning chunk {chunk_idx} containing {len(track_chunk)} tracks...")
        
        state = self.state_mgr.get_state()
        current_playlists: Dict[str, List[Dict[str, Any]]] = state.get("aligned_playlists", {})
        processed_tracks: List[str] = state.get("processed_tracks", [])
        processed_set = set(processed_tracks)

        aligned_results: List[Dict[str, Any]] = []
        newly_processed_ids: List[str] = []
        context_tax_accumulated: float = 0.0

        for track in track_chunk:
            track_id = str(track["track_id"])
            
            # Skip computation if this specific track ID was already committed in a previous transaction
            if track_id in processed_set:
                continue

            popularity = float(track.get("popularity", 0.5))
            genre = track.get("genre", "Unknown")
            is_local = str(track.get("is_local", False)).strip().lower() in ["true", "1", "t", "y", "yes"]

            if is_local and genre in [s.value for s in SouthAfricanSubgenre]:
                tau_c = popularity * 1.25
            elif not is_local:
                tau_c = -0.25 * popularity
            else:
                tau_c = 0.1

            refined_genre = self._classify_subgenre(track["title"], track["artist"], genre)

            aligned_record = {
                "track_id": track_id,
                "title": track["title"],
                "artist": track["artist"],
                "original_genre": genre,
                "aligned_genre": refined_genre,
                "context_tax_saved": max(0.0, tau_c)
            }

            aligned_results.append(aligned_record)
            newly_processed_ids.append(track_id)
            context_tax_accumulated += max(0.0, tau_c)

        # Idempotent playlist insertion: Deduplicate by track_id across target genre buckets
        for aligned in aligned_results:
            genre_bucket = aligned["aligned_genre"]
            if genre_bucket not in current_playlists:
                current_playlists[genre_bucket] = []

            existing_ids = {t["track_id"] for t in current_playlists[genre_bucket]}
            if aligned["track_id"] not in existing_ids:
                current_playlists[genre_bucket].append(aligned)

        # Update cumulative metrics and commit atomic state
        total_tax = state.get("metrics", {}).get("total_context_tax_saved", 0.0) + context_tax_accumulated
        updated_processed_tracks = list(processed_set.union(newly_processed_ids))

        self.state_mgr.update_state({
            "last_processed_chunk": chunk_idx,
            "processed_tracks": updated_processed_tracks,
            "aligned_playlists": current_playlists,
            "metrics": {
                "total_context_tax_saved": total_tax
            }
        })

        print(f"[CulturalAlignmentNode] Chunk {chunk_idx} aligned idempotently. Saved checkpoint.")
        return {
            "status": "SUCCESS",
            "chunk_idx": chunk_idx,
            "context_tax_saved": context_tax_accumulated,
            "new_tracks_aligned": len(aligned_results)
        }

    def _classify_subgenre(self, title: str, artist: str, original_genre: str) -> str:
        """
        Classifies a song using Gemini 3.5 Flash with structured JSON schema output,
        falling back to heuristic pattern matching if credentials or network fail.
        """
        if self.has_gemini:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client()
                prompt = (
                    f"You are a South African Music Ethnomusicologist.\n"
                    f"De-flatten this song from general categories (like 'World Music', 'Afrobeats', or 'Electronic') "
                    f"into a hyper-local South African subgenre.\n"
                    f"Title: \"{title}\" | Artist: \"{artist}\" | Original Genre: \"{original_genre}\""
                )

                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=SubgenreClassificationResponse,
                        temperature=0.1
                    )
                )

                parsed = SubgenreClassificationResponse.model_validate_json(response.text)
                return parsed.selected_subgenre.value

            except Exception as e:
                print(f"[CulturalAlignmentNode] Gemini structured inference failed: {e}. Falling back to heuristics.")

        # Deterministic heuristics fallback mapping prominent South African artists to genres
        artist_lower = artist.lower()
        if any(k in artist_lower for k in ["mthuda", "kabza", "kelvin momo", "de mthuda", "focalistic"]):
            return SouthAfricanSubgenre.AMAPIANO.value
        elif any(k in artist_lower for k in ["lag", "distruction boyz", "dj lag", "gqom"]):
            return SouthAfricanSubgenre.GQOM.value
        elif any(k in artist_lower for k in ["vetro", "shebeshxt", "king monada", "monada"]):
            return SouthAfricanSubgenre.LEKOMPO.value
        elif any(k in artist_lower for k in ["chana", "khuli chana", "morafe", "hhp", "motswako"]):
            return SouthAfricanSubgenre.MOTSWAKO.value
        elif any(k in artist_lower for k in ["mujava", "dj mujava", "spoko", "bacardi"]):
            return SouthAfricanSubgenre.BACARDI.value
        elif any(k in artist_lower for k in ["phuzekhemisi", "mroza", "shwi", "maskandi"]):
            return SouthAfricanSubgenre.MASKANDI.value

        return original_genre

# Georgia County List & GIS Boundary — Verified Data Sources

**Status:** Sources identified and verified. The actual data has **not** been downloaded or committed — this document records *where* to get it.

**Scope:** State of Georgia (FIPS state code **13**), all **159** counties (county FIPS `13001`–`13321`, odd numbers).

**How these were verified:** Each candidate URL was independently fetched and checked for three things — (1) hosted on an official U.S. federal or Georgia state government domain, (2) the page loads with real content, (3) the page actually contains or directly links to the claimed data. Only sources passing all three are listed as verified below.

---

## 1. County list (all 159 counties)

### ✅ U.S. Census Bureau — Georgia FIPS / County Subdivision file
- **URL:** https://www2.census.gov/geo/docs/reference/codes/files/st13_ga_cousub.txt
- **Agency:** U.S. Census Bureau (federal, `census.gov`)
- **Format:** Plain-text CSV
- **Contents:** All 159 Georgia counties with their FIPS codes and county subdivisions (e.g. `13001=Appling`, `13003=Atkinson`, `13005=Bacon`, …). Machine-readable and authoritative for county identity/codes.
- **Best for:** The canonical county list + FIPS codes to key every other dataset (turnout, demographics, GIS) against.

### ✅ Georgia Department of Revenue — County Tag Offices
- **URL:** https://dor.georgia.gov/county-tag-offices
- **Agency:** Georgia Department of Revenue (state, `dor.georgia.gov`)
- **Format:** HTML directory page
- **Contents:** Alphabetical listing of all 159 Georgia counties, each linking to that county's tax commissioner office.
- **Best for:** A human-readable state-government confirmation of the county list, and a jumping-off point to county-level offices. Less convenient than the Census file for programmatic use.

---

## 2. County GIS boundary data (shapefiles / geospatial)

### ✅ U.S. Census Bureau — TIGER/Line Shapefiles
- **URL:** https://www.census.gov/cgi-bin/geo/shapefiles/index.php
- **Agency:** U.S. Census Bureau, Geography Division (federal)
- **Format:** Esri Shapefile (ZIP)
- **Contents:** Interactive selector for county shapefiles by year (2007–2025; current 2025 release dated 2025-09-23). Select year → layer type "Counties" → Georgia. The most detailed/authoritative boundary geometry.
- **Best for:** Precise legal boundaries and joins on GEOID (`13` + county FIPS).

### ✅ U.S. Census Bureau — Cartographic Boundary Files (2019+)
- **URL:** https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html
- **Agency:** U.S. Census Bureau, Geography Division (federal)
- **Format:** Shapefile, KML, Geopackage, Geodatabase; resolutions 1:500k, 1:5m, 1:20m
- **Contents:** Simplified (generalized) county boundaries, better suited to web maps than full TIGER/Line. National file — filter to Georgia by state FIPS `13`.
- **Caveats:** (1) The data is national, not GA-specific downloads — you extract Georgia counties yourself. (2) GeoJSON is **not** among the offered formats here; convert from Shapefile/Geopackage if GeoJSON is needed for the web app.
- **Best for:** Lighter-weight boundaries for the SPA's eventual map view.

---

## Rejected / needs manual follow-up

- **❌ Census Cartographic Boundary Files — legacy page (1990–2018)** — https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html
  Official `census.gov` and live, but only offers **national** county files for 1990–2018 with no Georgia-specific path. Superseded by the 2019+ page above. Rejected as a distinct GA source.

- **⚠️ Georgia GIO Data Hub — "Counties" dataset** — https://data-hub.gio.georgia.gov/datasets/c28deb126b86434ebb3d576513054bf2
  Hosted on the **official Georgia Geospatial Information Office** domain (`gio.georgia.gov`) — i.e. the authoritative *state* GIS clearinghouse, which would be the ideal state-level counterpart to the federal Census sources. **Could not be auto-verified:** the page is JavaScript-rendered and an automated fetch saw only the title ("Counties 2018") with no visible download links or format metadata. **Recommended:** verify manually in a browser — if it exposes shapefile/GeoJSON/KML downloads as expected, it's worth promoting to a verified source (and may already provide GeoJSON directly, which the Census sources don't).

---

## Notes for downstream use

- **Keying:** Join county list, turnout, demographics, and GIS on county FIPS (`13xxx`) / GEOID rather than county name, to avoid name-spelling mismatches.
- **PII:** None of these sources contain PII — they are county identifiers and boundary geometry only, so derived data belongs in the normal project tree, not `sensitive-data/`.
- **Web app:** The SPA design anticipates a future map view. If/when that lands, the Cartographic Boundary (generalized) geometry converted to GeoJSON is the likely fit; TIGER/Line is the higher-fidelity fallback.

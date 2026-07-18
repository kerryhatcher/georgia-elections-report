# georgia-elections-report

A report covering elections administration, turnout, and voter demographics in the State of Georgia, USA.

## Scope

All data and analysis in this report pertain to the State of Georgia.

## Deliverables

### 1. County Boards of Elections Directory

A directory of all county boards of elections in Georgia (159 counties), including for each board:

- Current members
- Meeting location
- Meeting schedule (day/time, frequency)
- Method of selection (elected vs. appointed, and by whom)
- Recent news coverage and controversies

**Data sources:**

- Georgia Secretary of State, Elections Division (sos.ga.gov) — statewide elections directory and county contact list
- Individual county board of elections/registrar websites and published meeting agendas/minutes
- County boards each derive their composition and selection method from a **county-specific local act** of the Georgia General Assembly, not a single uniform state law — each county's enabling legislation must be looked up individually (available via the Georgia General Assembly's local legislation archive)
- Local and regional news archives (e.g. AJC, Georgia Recorder, county newspapers) for recent controversies
- Open Records Act (O.C.G.A. § 50-18-70 et seq.) requests to county boards for member rosters, meeting schedules, and minutes not published online

### 2. County-Level Turnout Rates (2026)

Voter turnout rate by county for every election held in Georgia during 2026 to date (including primaries, runoffs, and special elections), plus a statewide average/mean turnout for the year.

**Data sources:**

- Georgia Secretary of State, Elections Division — official certified results and turnout reports by county for each 2026 election
- Georgia My Voter Page (mvp.sos.ga.gov) — voter turnout statistics and absentee/early voting data
- County election superintendents' certified turnout reports (where SOS-published figures need corroboration)
- Registered-voter counts by county (denominator for turnout rate) from the Georgia voter registration file (see Deliverable 3)

### 3. Registered Voter Demographics

Demographic breakdown of registered voters, with the ability to filter and compare voters who cast a ballot against those who did not. Categories to include:

- Race/ethnicity, gender, and age
- Geography (county, precinct, and legislative district)
- Registration date / voter tenure
- Party affiliation (proxied via primary participation history, as Georgia does not register voters by party)

**Data sources:**

- Georgia Voter Registration List and Voter History File, obtained via Open Records request to the Georgia Secretary of State — the authoritative source for name, address, DOB, gender, race/ethnicity, county, precinct, registration date, and per-election voting history (which elections a voter participated in, not who they voted for)
- Party affiliation is derived, not stated: Georgia primary participation history (which party's primary a voter pulled) serves as the standard proxy
- These files contain PII and must be handled per the [Data Handling](#data-handling--pii) section below

## Data Handling & PII

Raw data files that contain or could be joined to reveal PII (the voter registration list, voter history file, and any derived extracts with individual-level records) go in [`sensitive-data/`](sensitive-data/README.md), which is git-ignored. Only de-identified, aggregated outputs (e.g. county-level turnout percentages, demographic summary tables) are committed to the repo.

Non-PII research — source lists, meeting schedule notes, official turnout/results reports, news clippings, aggregated public data — goes in [`docs/research/`](docs/research/README.md), which is tracked normally in git.


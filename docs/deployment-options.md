# Deployment Options for Open Data Coop Pipelines

## Goal
Enable individuals to easily run energy data pipelines against their own private data with minimal setup.

## Current State
- Pipelines: Green Button (utility data) + Home Assistant (real-time power monitoring)
- Stack: dlt (ingestion) → DuckDB (warehouse) → dbt (transformation) → Parquet (Paimon export)
- Dependencies: Managed via pixi (conda-forge + PyPI)
- Credentials needed: Home Assistant API, utility portal login, InfluxDB (optional)
- Storage: Local DuckDB files + Parquet warehouse

---

## Option 1: Fork + Local Config (Recommended for Privacy-First)

### Approach
Users fork the repo and add their own `.env` or `config.local.yml` file (gitignored) containing credentials and paths.

### Implementation
```yaml
# config.example.yml (checked into repo)
storage:
  warehouse_dir: ~/energy-data/warehouse
  duckdb_path: energy_warehouse.duckdb

sources:
  green_button:
    enabled: true
    xml_files_dir: ~/Downloads/green_button
    home_id: YOUR_HOME_ID  # Replace with your identifier

  home_assistant:
    enabled: true
    influxdb_url: http://localhost:8086
    influxdb_token: YOUR_TOKEN  # Add to config.local.yml
    influxdb_org: home
    influxdb_bucket: power_monitoring

schedule:
  green_button: manual  # or "weekly"
  home_assistant: hourly

exports:
  paimon:
    enabled: true
    partitions:
      electricity_consumption: [home_id, year, month]
      power_monitoring: [home_id, device_id]
```

### User Setup Flow
```bash
# 1. Fork repo
# 2. Clone locally
git clone https://github.com/YOUR_USERNAME/open-data-coop.git
cd open-data-coop

# 3. Install dependencies
pixi install

# 4. Copy config template
cp config.example.yml config.local.yml

# 5. Edit config with your credentials
nano config.local.yml

# 6. Run pipelines
pixi run pipeline-green-button    # Manual Green Button import
pixi run pipeline-home-assistant  # Continuous HA monitoring
pixi run export-paimon            # Export to warehouse
```

### Pros
- ✅ **Maximum privacy**: Data never leaves user's machine
- ✅ **Full control**: Users own their fork and data
- ✅ **Simple setup**: Just edit one config file
- ✅ **Flexible**: Easy to customize pipelines
- ✅ **Version control**: Users can track their config changes (in private repo)
- ✅ **No ongoing costs**: Runs locally on user hardware

### Cons
- ❌ **Git knowledge required**: Users need basic git/GitHub skills
- ❌ **Local resource usage**: Requires user's machine to run pipelines
- ❌ **No automatic updates**: Users must manually merge upstream changes
- ❌ **Limited collaboration**: Each user has isolated instance

### Best For
- Privacy-conscious users
- Technical users comfortable with git/CLI
- Small-scale personal deployments
- Users who want full control

---

## Option 2: Docker Compose Template

### Approach
Provide a `docker-compose.yml` with all services pre-configured. Users only need Docker and their credentials.

### Implementation
```yaml
# docker-compose.yml
services:
  pipelines:
    build: .
    volumes:
      - ./config.local.yml:/app/config.local.yml:ro
      - ./data:/app/data
      - ~/energy-data:/app/warehouse
    environment:
      - HOME_ASSISTANT_TOKEN=${HA_TOKEN}
      - INFLUXDB_TOKEN=${INFLUXDB_TOKEN}
    command: python -m pipelines.scheduler

  duckdb:
    image: duckdb/duckdb:latest
    volumes:
      - ./data:/data
    command: /data/energy_warehouse.duckdb

  scheduler:
    image: ofelia:latest
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    labels:
      ofelia.job-exec.green-button.schedule: "@weekly"
      ofelia.job-exec.home-assistant.schedule: "@hourly"
```

### User Setup Flow
```bash
# 1. Download template
curl -o docker-compose.yml https://raw.githubusercontent.com/ryanfobel/open-data-coop/main/docker-compose.yml

# 2. Create .env file
cat > .env <<EOF
HA_TOKEN=your_home_assistant_token
INFLUXDB_TOKEN=your_influxdb_token
HOME_ID=your_home_id
EOF

# 3. Run
docker compose up -d
```

### Pros
- ✅ **Easy setup**: No Python/pixi installation needed
- ✅ **Isolated**: Containers don't interfere with system
- ✅ **Portable**: Works on any OS with Docker
- ✅ **Built-in scheduling**: Can run continuously
- ✅ **Resource limits**: Can cap CPU/memory usage

### Cons
- ❌ **Docker overhead**: Requires Docker Desktop (paid for business)
- ❌ **Less flexible**: Harder to customize without rebuilding
- ❌ **Opaque**: Harder to debug than native Python
- ❌ **Image size**: Docker images can be large

### Best For
- Non-technical users who just want it to work
- Users running on a home server/NAS
- Multi-user households (one instance for whole home)

---

## Option 3: GitHub Actions + Cloud Storage

### Approach
Pipelines run as scheduled GitHub Actions. Results stored in user's cloud storage (S3/GCS/Azure).

### Implementation
```yaml
# .github/workflows/pipeline.yml
name: Energy Data Pipeline
on:
  schedule:
    - cron: '0 * * * *'  # Hourly
  workflow_dispatch:

jobs:
  home-assistant:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: prefix-dev/setup-pixi@v1
      - run: pixi run pipeline-home-assistant
      - name: Upload to S3
        run: |
          pixi run aws s3 sync ~/energy-data s3://${{ secrets.S3_BUCKET }}/warehouse
```

### User Setup Flow
```bash
# 1. Fork repo
# 2. Add secrets in GitHub Settings:
#    - HA_TOKEN
#    - INFLUXDB_TOKEN
#    - AWS_ACCESS_KEY_ID
#    - AWS_SECRET_ACCESS_KEY
#    - S3_BUCKET

# 3. Enable GitHub Actions
# 4. Pipelines run automatically
```

### Pros
- ✅ **Zero local infrastructure**: Runs in GitHub's cloud
- ✅ **Free tier available**: 2,000 minutes/month for private repos
- ✅ **Automatic scheduling**: Built-in cron support
- ✅ **Version controlled**: Pipeline code and results versioned together
- ✅ **No maintenance**: No servers to manage

### Cons
- ❌ **Credentials in GitHub**: Secrets stored in GitHub (though encrypted)
- ❌ **Limited to 6 hour runs**: GitHub Actions timeout
- ❌ **Costs for cloud storage**: S3/GCS fees (though minimal for this use case)
- ❌ **Less privacy**: Data passes through GitHub runners
- ❌ **Debugging harder**: Can't easily attach debugger

### Best For
- Users who want "set and forget" automation
- Users already paying for cloud storage
- Users comfortable with cloud providers
- Users who want audit logs (GitHub Actions history)

---

## Option 4: Cookiecutter Template Project

### Approach
Provide a cookiecutter template that generates a customized project structure during setup.

### Implementation
```bash
cookiecutter gh:ryanfobel/energy-pipeline-template

# Prompts:
# - Project name: my-energy-data
# - Home ID: home-001
# - Enable Green Button? [y/n]: y
# - Enable Home Assistant? [y/n]: y
# - InfluxDB URL: http://localhost:8086
# - Warehouse path: ~/energy-data
```

Generates:
```
my-energy-data/
├── config.yml           # Pre-filled with your answers
├── pipelines/
│   ├── green_button/
│   └── home_assistant/
├── transform/           # dbt models
├── scripts/
│   ├── run_green_button.py
│   └── run_home_assistant.py
└── README.md           # Customized instructions
```

### Pros
- ✅ **Guided setup**: Interactive prompts prevent configuration errors
- ✅ **Clean slate**: No repo clutter from disabled features
- ✅ **Custom README**: Documentation tailored to user's config
- ✅ **Best practices**: Template enforces good patterns
- ✅ **Updatable**: Can pull template updates via cruft

### Cons
- ❌ **Extra tool**: Users need to install cookiecutter
- ❌ **Disconnected from upstream**: Not a fork, harder to contribute back
- ❌ **Template maintenance**: Need to keep template in sync with main repo

### Best For
- Users starting fresh (not forking)
- Users who want a streamlined, minimal setup
- Educational use (schools, workshops)

---

## Option 5: Web App (Evidence.dev Dashboard)

### Approach
Deploy Evidence.dev dashboard that allows users to configure and run pipelines via web UI.

### Implementation
```
User visits: https://energy-dashboard.app
1. Create account
2. Configure data sources (forms for InfluxDB, Green Button upload)
3. Schedule pipelines (dropdowns for frequency)
4. View results in dashboard

Backend:
- FastAPI server runs pipelines on user trigger
- Results stored in user's DuckDB (isolated per account)
- Evidence.dev renders charts from DuckDB
```

### Pros
- ✅ **No technical skills**: Point-and-click interface
- ✅ **Instant feedback**: See pipeline results immediately
- ✅ **Collaborative**: Share dashboards with family/housemates
- ✅ **Mobile friendly**: Check energy usage from phone

### Cons
- ❌ **Privacy concerns**: Data goes to third-party server
- ❌ **Hosting costs**: Need to run server infrastructure
- ❌ **Development effort**: Significant build required
- ❌ **Ongoing maintenance**: Server monitoring, updates, backups

### Best For
- Non-technical users
- Community deployments (coops, condos)
- Users who value convenience over privacy

---

## Comparison Matrix

| Feature | Fork+Local | Docker | GitHub Actions | Cookiecutter | Web App |
|---------|-----------|--------|---------------|--------------|---------|
| Privacy | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Ease of Setup | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Customization | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| Automation | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Cost (monthly) | $0 | $0 | $0-5 | $0 | $10-50 |
| Technical Skill | High | Medium | Medium | Medium | Low |
| Update Path | Manual merge | Pull image | Fork sync | Template update | Automatic |

---

## Recommendation: Hybrid Approach

**Primary: Fork + Local Config (Option 1)**
- Best privacy-to-ease ratio
- Aligns with open-source ethos
- Users maintain control

**Optional: Docker Compose (Option 2)**
- For users who want "always on" automation
- Provide as `docker-compose.yml` in repo

**Future: Web App (Option 5)**
- Once pipelines are stable
- For community/coop deployments
- Open-source the server (users can self-host)

---

## Implementation Checklist

### Phase 1: Fork + Local Config (Now)
- [ ] Create `config.example.yml` with all settings
- [ ] Add `.gitignore` entries for `config.local.yml`, `*.duckdb`, `data/`
- [ ] Write config loader in `pipelines/config.py`
- [ ] Update all scripts to read from config
- [ ] Write comprehensive setup guide in `README.md`
- [ ] Add `pixi run` tasks for common operations
- [ ] Test on fresh clone

### Phase 2: Docker Support (Next)
- [ ] Create `Dockerfile`
- [ ] Create `docker-compose.yml`
- [ ] Add health checks for services
- [ ] Test on Linux/Mac/Windows
- [ ] Document Docker setup in `docs/docker.md`

### Phase 3: Template (Optional)
- [ ] Extract to cookiecutter template
- [ ] Add CI to test template generation
- [ ] Document in separate repo

### Phase 4: Web App (Future)
- [ ] Design multi-tenant architecture
- [ ] Build FastAPI backend
- [ ] Integrate Evidence.dev
- [ ] Add authentication (OAuth)
- [ ] Deploy to cloud

---

## Security Considerations

### Credentials Storage
1. **Never commit**: `.env`, `config.local.yml`, API tokens
2. **Example files**: Always provide `.example` versions
3. **Encryption**: Consider encrypting sensitive config with `age` or `sops`
4. **Rotation**: Document how to rotate credentials

### Data Privacy
1. **Local-first**: Default to local storage
2. **Anonymization**: Provide option to hash `home_id`
3. **Retention**: Document data retention policies
4. **GDPR**: Add data export/deletion scripts

### API Access
1. **Rate limiting**: Respect API rate limits (InfluxDB, HA)
2. **Readonly**: Use read-only tokens when possible
3. **Scoping**: Request minimal OAuth scopes

---

## Sample `config.example.yml`

```yaml
# Open Data Coop - Energy Pipeline Configuration
# Copy to config.local.yml and fill in your values

project:
  name: my-energy-data
  home_id: YOUR_HOME_ID  # Unique identifier (can be anything)

storage:
  warehouse_dir: ~/energy-data/warehouse
  duckdb_path: energy_warehouse.duckdb

sources:
  green_button:
    enabled: true
    xml_files_dir: ~/Downloads/green_button
    auto_import: false  # Set to true to monitor directory

  home_assistant:
    enabled: false
    influxdb:
      url: http://localhost:8086
      org: home
      bucket: power_monitoring
      token: ${INFLUXDB_TOKEN}  # Set in environment or .env file

    # Alternative: Direct HA API
    # api:
    #   url: http://homeassistant.local:8123
    #   token: ${HA_TOKEN}
    #   entities:
    #     - sensor.emporia_vue_power
    #     - sensor.iotawatt_main_1

exports:
  paimon:
    enabled: true
    warehouse_dir: ~/energy-data/warehouse
    partitions:
      electricity_consumption: [home_id, year, month]
      power_monitoring: [home_id, device_id]

  evidence:
    enabled: false
    output_dir: ~/energy-data/evidence

dbt:
  profiles_dir: transform
  target: dev
  threads: 4

logging:
  level: INFO
  file: logs/pipeline.log
```

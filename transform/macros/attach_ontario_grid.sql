{% macro attach_ontario_grid() %}
    {% set query %}
        ATTACH IF NOT EXISTS '/Users/ryan/dev/open-data-coop/projects/ontario-grid-pipelines/ontario-grid-pipelines/dashboard/sources/ontario_grid/ontario_grid.duckdb' AS ontario_grid (READ_ONLY)
    {% endset %}
    {% do run_query(query) %}
{% endmacro %}

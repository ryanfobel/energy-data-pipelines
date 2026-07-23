{% macro attach_raw_data() %}
    {% set query %}
        ATTACH IF NOT EXISTS '../green_button.duckdb' AS green_button (READ_ONLY);
        ATTACH IF NOT EXISTS '../weather.duckdb' AS weather (READ_ONLY);
    {% endset %}
    {% do run_query(query) %}
{% endmacro %}

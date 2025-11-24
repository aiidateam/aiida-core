window.CONFIGURATION_DATA = {
    "suites": {
        "pytest-benchmarks:ubuntu-18.04,django": {
            "header": "Performance Benchmarks (Ubuntu-18.04, Django)",
            "description": "Performance benchmark tests, generated using pytest-benchmark."
        },
        "pytest-benchmarks:ubuntu-18.04,sqlalchemy": {
            "header": "Performance Benchmarks (Ubuntu-18.04, SQLAlchemy)",
            "description": "Performance benchmark tests, generated using pytest-benchmark."
        },
        "pytest-benchmarks:ubuntu-18.04,psql_dos": {
            "header": "Performance Benchmarks (Ubuntu-18.04)",
            "description": "Performance benchmark tests, generated using pytest-benchmark."
        },
        "pytest-benchmarks:ubuntu-22.04,psql_dos": {
            "header": "Performance Benchmarks (Ubuntu-22.04)",
            "description": "Performance benchmark tests, generated using pytest-benchmark."
        }

    },
    "groups": {
        "node": {
            "header": "Single Node",
            "description": "Comparison of basic node interactions, such as storage and deletion from the database.",
            "single_chart": true,
            "xAxis": "id",
            "backgroundFill": false,
            "yAxisFormat": "logarithmic"
        },
        "engine": {
            "header": "Processes",
            "description": "Comparison of Processes, executed via both local and daemon runners.",
            "single_chart": true,
            "xAxis": "id",
            "backgroundFill": false,
            "legendAlign": "start",
            "yAxisFormat": "logarithmic"
        },
        "import-export": {
            "header": "Import-Export",
            "description": "Comparison of import/export of provenance trees.",
            "single_chart": true,
            "xAxis": "id",
            "backgroundFill": false,
            "yAxisFormat": "logarithmic"
        },
        "large-archive": {
            "header": "large-archive",
            "description": "Comparison of import/export of large archives.",
            "single_chart": true,
            "xAxis": "id",
            "backgroundFill": false,
            "yAxisFormat": "logarithmic"
        }
    }
}

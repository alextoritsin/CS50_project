$(document).ready(function() {
        $("#one").on("click", function() {
            Plotly.purge('chart');
            var graphs1 = {{ g_JSON_one | safe }};
            Plotly.react("chart", graphs1, {});
        });
        $("#two").on("click", function() {
            Plotly.purge('chart');
            var graphs2 = {{ g_JSON_two | safe }};
            Plotly.react("chart", graphs2, {});
        });
        $("#five").on("click", function() {
            Plotly.purge('chart');
            var graphs5 = {{ g_JSON_five | safe }};
            Plotly.react("chart", graphs5, {});
        })
    });
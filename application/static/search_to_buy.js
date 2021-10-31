// Create an array of companies
var companies  = [];

function loadComp(){
    $.getJSON('/companies', function(data, status, xhr){
        for (var i = 0; i < data.length; i++) {
            companies.push(data[i]);
        }
    });
};
loadComp();

$(document).ready(function() {
    

    // Overrides the default autocomplete filter function
    // to search only from the beginning of the string
    $.ui.autocomplete.filter = function (array, term) {
        var matcher = new RegExp("^" + $.ui.autocomplete.escapeRegex(term), "i");
        return $.grep(array, function (value) {
            return matcher.test(value.label || value.value || value);
        });
    };
    // split and extract functions
    function split( val ) {
        return val.split( /,\s*/ );
    }
    function extractLast( term ) {
    return split( term ).pop();
    }

    // Initialize jquery autocomplete
    $("#symbol").autocomplete( {
        minLength: 3,
        autoFocus: true,
        source: function (request, response) {
            var results = $.ui.autocomplete.filter(companies, extractLast(request.term));
            response(results.slice(0, 10));
        }
        
    });
});
    
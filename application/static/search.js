$(document).ready(function() {
    var availableTags = [
        "C++", "Python", "PHP", "Java", "C", "Ruby",
        "R", "C#", "Dart", "Fortran", "Pascal", "Javascript"
    ];
    $("#name").autocomplete( {
        source: availableTags
    });
});

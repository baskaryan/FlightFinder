$(document).ready(function() {
    $( "#city" ).autocomplete({
        source: function( request, response ) {
            $.ajax({
                url: "http://api.sandbox.amadeus.com/v1.2/airports/autocomplete",
                dataType: "json",
                data: {
                    apikey: "4kLFYfEgqIjGCLli8wtsKYYOAZJG4QCg",
                    term: request.term
                },
                success: function( data ) {
                    response( data );
                }           
            });
        },
        minLength: 2
    }); 
});
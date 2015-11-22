$(document).ready(function() {
    $("#submit-id-submit").attr("data-loading-text", "Signing in...");
    $("#submit-id-submit").click(function(){
        $(this).button('loading');
        console.log("Woah!");
    })
});
$(document).ready(function() {
//Setting the highlighted tab in the nav bar.
    $("#home_tab").addClass("active");

    $("#force-srs").click(function(){
        $.get("/kw/force_srs/").done(function(data){
           alert(data)
        });
    })
});
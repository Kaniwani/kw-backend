$(document).ready(function() {
//Setting the highlighted tab in the nav bar.
    $("#home_tab").addClass("active");

    $("#force-srs").click(function(){
        $.get("/kw/force_srs/").done(function(data){
            if (parseInt(data) > 0){
                $("#review-count").html(data + " Reviews");
                $("#review-count").removeClass("disabled");
            }

        });
    });

     //Binding R/S/H/U/C to refresh/start reviews/about/unlocks/contact
     $(document).keypress(function(e){
        if (e.which == 83 || e.which == 115) {
            window.location.href = "/kw/review/"
        }
        else if (e.which == 82 || e.which == 114) {
            $("#force-srs").click();
            //as it needs a custom handler.
        }
        else if (e.which == 72 || e.which == 104) {
            window.location.href = "/kw/about/"
        }
        else if (e.which == 85 || e.which == 117) {
            window.location.href = "/kw/unlocks/"
        }
        else if (e.which == 67 || e.which == 99) {
            window.location.href = "/kw/contact/"
        }

    });
});
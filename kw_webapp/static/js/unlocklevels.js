$(document).ready(function() {
    var csrf_token = $("#csrf").val();
    //Setting the highlighted tab in the nav bar.
    $("#unlocks_tab").addClass("active");

    $(".locked").click(function(){
        var requested_level = $(this).attr("id");
        console.log("woo");
        $.post("/kw/levelunlock/", {level: requested_level, csrfmiddlewaretoken:csrf_token}).done(function(data) {
            alert(data);
        })
    });

});
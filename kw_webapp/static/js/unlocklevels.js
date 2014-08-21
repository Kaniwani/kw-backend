$(document).ready(function() {
    var csrf_token = $("#csrf").val();

    $(".locked").click(function(){
        var requested_level = $(this).attr("id");
        console.log("woo");
        $.post("/kw/levelunlock/", {level: requested_level, csrfmiddlewaretoken:csrf_token}).done(function(data) {
            alert(data);
        })
    });

});
$(document).ready(function() {
    var csrf_token = $("#csrf").val();
    //Setting the highlighted tab in the nav bar.
    $("#unlocks_tab").addClass("active");

    $(".locked").click(function(){
        var requested_level = $(this).attr("id");
        var list_item = $(this)
        console.log("woo");
        $.post("/kw/levelunlock/", {level: requested_level, csrfmiddlewaretoken:csrf_token}).done(function(data) {
            list_item.removeClass("list-group-item-warning");
            list_item.removeClass("locked");
            list_item.addClass("list-group-item-success");
            list_item.html("Level " + requested_level + " Unlocked")
            alert(data);
        })
    });

});
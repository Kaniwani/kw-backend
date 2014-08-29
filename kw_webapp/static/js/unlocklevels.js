$(document).ready(function() {
    var csrf_token = $("#csrf").val();
    //Setting the highlighted tab in the nav bar.
    $("#unlocks_tab").addClass("active");
    $.notify.defaults({position:"right", autoHideDelay:2000});
    $(".unlockable").click(function(event){
        event.preventDefault();
        var requested_level = $(this).attr("id");
        var list_item = $(this);
        $.post("/kw/levelunlock/", {level: requested_level, csrfmiddlewaretoken:csrf_token}).done(function(data) {
            list_item.removeClass("list-group-item-warning");
            list_item.removeClass("locked");
            list_item.addClass("list-group-item-success");
            list_item.html("Level " + requested_level + " Unlocked");
            list_item.notify(
                data + " vocabulary unlocked.",
                {
                    className:"success",
                }
            )
        })
    });

    $(".locked").click(function(event) {
        event.preventDefault();
        var list_item = $(this);
        list_item.notify(
                "I'm Sorry, I can't let you do that. ",
                {
                    className:"danger",
                }
            )
    });

    $(".unlocked").click(function(event) {
        event.preventDefault();
        var list_item = $(this);
        list_item.notify(
                "Already Unlocked!",
                {
                    className:"info",
                }
            )
    });


});
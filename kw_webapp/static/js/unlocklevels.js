$(document).ready(function() {
    var csrf_token = $("#csrf").val();
    //Setting the highlighted tab in the nav bar.
    $("#unlocks_tab").addClass("active");
    $(".image").hide();
    $.notify.defaults({
        position: "right",
        autoHideDelay: 5000
    });

    //When you click on an unlockable(yellow) level
    $(".unlockable").click(function(event){
        event.preventDefault();
        var requested_level = $(this).attr("id");
        var list_item = $(this);
        // TODO: @djtb use remodal or cferdinandi modal for confirmation
        list_item.find("img").show();
        $.post("/kw/levelunlock/", {level: requested_level, csrfmiddlewaretoken:csrf_token}).done(function(data) {
            list_item.removeClass("list-group-item-warning");
            list_item.removeClass("unlockable");
            list_item.addClass("unlocked");
            list_item.addClass("list-group-item-success");
            list_item.find("img").hide();
            list_item.find("p").text("Level " + requested_level + " Unlocked");
            list_item.notify(data, { className:"success" });
        });
    });

    $(".locked").click(function(event) {
        event.preventDefault();
        var list_item = $(this);
        list_item.notify("I'm Sorry, I can't let you do that. ", { className:"danger" });
    });

    // TODO: @tadgh, this should have a POST to relock a level <3
    $(".unlocked").click(function(event) {
        event.preventDefault();
        var list_item = $(this);
        list_item.notify("Already Unlocked!", { className:"info" });
    });


});

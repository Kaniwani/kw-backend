$(document).ready(function() {
    var csrf_token = $("#csrf").val();

    $(document).on("click", ".level__item--locked", function(event) {
        event.preventDefault();
        var item = $(this);
        var child_icon_span = item.find(".fa-unlock-alt");
        var level = item.data("level-id");
        console.log(Date.now());
        $.post("/kw/levelunlock/", {"level": level, csrfmiddlewaretoken:csrf_token}).done(function(data) {
            console.log(Date.now());
            console.log(child_icon_span);
            child_icon_span.removeClass("fa-unlock-alt");
            child_icon_span.addClass("fa-unlock");
            item.removeClass("level__item--locked");
        });
        event.stopPropagation();
    });
});
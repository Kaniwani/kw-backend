// lock endpoint is just /kw/levellock

$(document).ready(function() {
    var csrf_token = $("#csrf").val();

    $('body').on("click", ".level__item--locked", function(event) {
        event.preventDefault();
        var item = $(this);
        var child_icon_span = item.find(".fa-unlock-alt");
        var level = item.data("level-id");
        $.post("/kw/levelunlock/", {"level": level, csrfmiddlewaretoken:csrf_token}).done(function(data) {
            child_icon_span.removeClass("fa-unlock-alt");
            child_icon_span.addClass("fa-unlock");
            item.removeClass("level__item--locked");
        });
        event.stopPropagation();
    });
});

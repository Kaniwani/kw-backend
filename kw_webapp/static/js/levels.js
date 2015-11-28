$(document).ready(function() {
    var csrf_token = $("#csrf").val();

    $(document).on("click", ".level__item--locked", function(event) {
        event.preventDefault();
        var item = $(this);
        var child_icon_span = item.find(".fa-lock");
        var level = item.data("level-id");
        $.post("/kw/levelunlock/", {"level": level, csrfmiddlewaretoken:csrf_token}).done(function(data) {
            console.log(data);
            child_icon_span.removeClass("fa-lock");
            child_icon_span.addClass("fa-unlock");
            item.removeClass(".level__item--locked");
        });
        event.stopPropagation();
    });
});
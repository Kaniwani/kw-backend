$(document).ready(function() {
    var csrf_token = $("#csrf").val();
    $(".fa-unlock").click(function(event) {
        event.preventDefault();
        var review_pk = $(this).data("pk");
        var item = $(this);
         $.post("/kw/togglevocab/", {"review_id": review_pk, csrfmiddlewaretoken:csrf_token}).done(function(data) {
             console.log(data);
             item.removeClass("fa-unlock");
             item.addClass("fa-lock");
        });
    });

    $(".fa-lock").click(function(event) {
        event.preventDefault();
        var review_pk = $(this).data("pk");
        var item = $(this);
        $.post("/kw/togglevocab/", {"review_id": review_pk, csrfmiddlewaretoken:csrf_token}).done(function(data) {
            console.log(data);
            item.removeClass("fa-lock");
            item.addClass("fa-unlock");
        });
    });
});
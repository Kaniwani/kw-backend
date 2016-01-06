$(document).ready(function() {
    var csrf_token = $("#csrf").val();
    $('body').on("click", ".i-unlock", function(event) {
        event.preventDefault();
        var $this = $(event.target);
        var review_pk = $this.data("pk");
        var item = $this;
         $.post("/kw/togglevocab/", {"review_id": review_pk, csrfmiddlewaretoken:csrf_token}).done(function(data) {
             console.log(data);
             item.removeClass("i-unlock");
             item.addClass("i-unlocked");
        });
    });

    $("body").on("click", ".i-unlocked", function(event) {
        event.preventDefault();
        var $this = $(event.target);
        var review_pk = $this.data("pk");
        var item = $this;
        $.post("/kw/togglevocab/", {"review_id": review_pk, csrfmiddlewaretoken:csrf_token}).done(function(data) {
            console.log(data);
            item.removeClass("i-unlocked");
            item.addClass("i-unlock");
        });
    });
    //TODO @Subversity. You will notice that these functions are damn near identical. They both hit the same endpoint, which just toggles current hidden status. Can probably refactor this JS?
});
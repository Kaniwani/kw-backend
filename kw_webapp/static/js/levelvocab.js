// this file no longer loaded
// refactored and active in webapp template via toolkit/scripts/sections/vocab.js

function toggleClasses($icon, $card) {
    $card.toggleClass('-locked -unlockable');
    $icon.toggleClass("i-unlock").toggleClass("i-unlocked");
}

$(document).ready(function() {
    var csrf_token = $("#csrf").val();
    $('.vocab-list').on("click", ".icon", function(event) {

        var $icon = $(event.target),
            $card = $icon.closest('.vocab-card')
            review_pk = $card.data("pk");

         $.post("/kw/togglevocab/", {"review_id": review_pk, csrfmiddlewaretoken:csrf_token}).done(function(data) {
            console.log(data);
            toggleClasses($icon, $card);
        });
    });
});

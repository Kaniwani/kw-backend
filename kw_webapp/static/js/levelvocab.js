$(document).ready(function() {
    var csrf_token = $("#csrf").val();
    $.notify.defaults({
            position:"left",
            autoHideDelay:1000
            });
      //When you click on an unlockable(yellow) level
    $(".togglehide").click(function(event){
        console.log("Clicked on a togglehide!")
        event.preventDefault();
        var review_id = $(this).attr("id");
        var button = $(this);
        $.post("/kw/togglevocab/", {review_id: review_id,  csrfmiddlewaretoken: csrf_token}).done(function(data) {

            if(button.hasClass("btn-success")){
                button.removeClass("btn-success");
                button.addClass("btn-danger");
                button.text("Lock")
            }else{
                button.removeClass("btn-danger");
                button.addClass("btn-success");
                button.text("Unlock")
            }
            button.notify(
                data,
                {
                    className:"success"
                }
            )
        })
    });
});
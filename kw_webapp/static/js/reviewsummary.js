$(document).ready(function() {
    $("#correct_jumbo").hide();
    $("#incorrect_jumbo").hide();

    $("#correct-expand-button").click(function(){
        $("#correct_jumbo").toggle();
    });

    $("#incorrect-expand-button").click(function(){
        $("#incorrect_jumbo").toggle();
    });

});
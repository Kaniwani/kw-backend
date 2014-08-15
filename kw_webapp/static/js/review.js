$(document).ready(function() {
    var input = document.getElementById("user-answer");
    wanakana.bind(input);

    var correct_answers = new Array();
    var incorrect_answers = new Array();
    function compareAnswer(){
       var us_id;
       var answer;
       var correct;
       us_id = $("#us-id").val();
       answer = $("#user-answer").val();

       if (!wanakana.isHiragana(answer) || answer == '') {
           $("#user-answer").css('background-color', 'yellow');
           return
       }
       else if ($.inArray(answer, current_vocab.readings) == 0) {
           if($.inArray(current_vocab.meaning, incorrect_answers) != 0) {
               correct_answers.push(current_vocab.meaning);
           }

           $("#user-answer").css('background-color', 'green');
           correct = true;
           $("#user-answer").addClass("marked");
           fill_text_with_kanji();
       }
       else{
           if($.inArray(current_vocab.meaning, incorrect_answers) != 0) {
               incorrect_answers.push(current_vocab.meaning);
           }

            vocabulary_list.push(current_vocab);
            $("#user-answer").css('background-color', 'red');

            correct = false;
           $("#user-answer").addClass("marked");
       }
       enableButtons();
       $.post("/kw/record_answer/", {user_specific_id:us_id, user_correct:correct}, function(data) {

       })
    }

    function disableButtons(){
        $("#button-reading").prop("disabled", "disabled");
        $("#button-reading").removeClass("btn-primary");
        $("#button-reading").addClass("btn-default");
        $("#button-character").prop("disabled", "disabled");
        $("#button-character").removeClass("btn-primary");
        $("#button-character").addClass("btn-default");
    }
    function enableButtons(){
        $("#button-reading").prop("disabled", "");
        $("#button-reading").removeClass("btn-default");
        $("#button-reading").addClass("btn-primary");
        $("#button-character").prop("disabled", "");
        $("#button-character").removeClass("btn-default");
        $("#button-character").addClass("btn-primary");
    }
    function fill_text_with_kanji(){
        $("#user-answer").val(current_vocab.characters);
    }
    function rotateVocab(){
        if (vocabulary_list.length == 0){
            alert("Out of reviews!");
            return
        }
        current_vocab = vocabulary_list.shift();
        $("#details-reading").hide();
        $("#details-character").hide();
        disableButtons();
        $("#meaning").html(current_vocab.meaning);
        $("#us-id").val(current_vocab.user_specific_id);
        $("#kana").html(current_vocab.readings);
        $("#character").html(current_vocab.characters);

        $("#user-answer").val("");
        $("#user-answer").css('background-color', 'white');

    }
    function enterClicked(){
        compareAnswer();
        rotateVocab();
    }

    $(document).keypress(function(e){
    if (e.which == 13){
        $("#check").click();
    }
});

  var vocab_list = [];
   $("#check").click(function() {
       if($("#user-answer").hasClass("marked")){
           rotateVocab();
           $("#user-answer").removeClass("marked");
       }
       else {
           compareAnswer();

       }
   });

   $("#button-reading").click(function() {
       $("#details-reading").toggle();
   });

    $("#button-character").click(function() {
       $("#details-character").toggle();
   });

});

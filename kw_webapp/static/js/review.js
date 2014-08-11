$(document).ready(function() {
    var input = document.getElementById("user-answer");
    wanakana.bind(input);
    function compareAnswer(){
       var us_id;
       var answer;
       var correct;
       us_id = $("#us-id").val();
       answer = $("#user-answer").val();


       if ($.inArray(answer, current_vocab.readings) == 0) {
           $("#user-answer").css('background-color', 'green');
           correct = true;
       }
       else{
            vocabulary_list.push(current_vocab);
            $("#user-answer").css('background-color', 'red');
            $("#details").show();
            correct = false;
       }



       $.post("/kw/record_answer/", {user_specific_id:us_id, user_correct:correct}, function(data) {
           console.log("Got an answer!" + data);
       })
    }


    function rotateVocab(){
        current_vocab = vocabulary_list.shift();
        $("#details").hide();
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
           $("#user-answer").addClass("marked");
       }
   })
});
$(document).ready(function() {
    var input = document.getElementById("user-answer");
    var csrf_token = $("#csrf").val();//Grab CSRF token off of dummy form.
    wanakana.bind(input);

    var correct_answers = new Array();
    var incorrect_answers = new Array();
    var answer_correctness = new Array();

    function make_post(path, params) {
       var form = document.createElement("form");
       form.setAttribute("method", "post");
       form.setAttribute("action", path);

       for(var key in params) {
           if(params.hasOwnProperty(key)) {
               var hiddenField = document.createElement("input");
               hiddenField.setAttribute("type", "hidden");
               hiddenField.setAttribute("name", key);
               hiddenField.setAttribute("value", params[key]);

               form.appendChild(hiddenField);
           }
       }
       //CSRF hackery.
       csrf_field = document.createElement("input");
       csrf_field.setAttribute("name", "csrfmiddlewaretoken");
       csrf_field.setAttribute("value", csrf_token);
       form.appendChild(csrf_field);
       document.body.appendChild(form);
       form.submit();
   }

    function compareAnswer(){
       var us_id;
       var answer;
       var correct;
       us_id = $("#us-id").val();
       answer = $("#user-answer").val();

        console.log("comparing")
       if (!wanakana.isHiragana(answer) || answer == '')
       {
           nonHiraganaAnswer();
           return;
       }
       else if ($.inArray(answer, current_vocab.readings) != -1)
       {
           if($.inArray(current_vocab.meaning, Object.keys(answer_correctness)) == -1) {
               answer_correctness[current_vocab.meaning] = true;
           }
           rightAnswer();
           correct = true;
           var answer_index = $.inArray(answer, current_vocab.readings);
           fill_text_with_kanji(answer_index); //Fills the correct kanji based on the user's answers.
       }
       else
       {
           if($.inArray(current_vocab.meaning, incorrect_answers) == -1) {
               answer_correctness[current_vocab.meaning] = false;
           }
           wrongAnswer();
           correct = false;

       }
       enableButtons();
       $.post("/kw/record_answer/", {user_specific_id:us_id, user_correct:correct, csrfmiddlewaretoken:csrf_token}, function(data) {
            console.log(data)
       })
    }

    function nonHiraganaAnswer(){
        $("#user-answer").css('background-color', 'yellow');
    }

    function wrongAnswer(){
        vocabulary_list.push(current_vocab);
        $("#user-answer").css('background-color', 'red');
        $("#user-answer").addClass("marked");
        $("#user-answer").blur();
    }

    function rightAnswer(){
        $("#user-answer").css('background-color', 'green');
        $("#user-answer").blur();
        $("#user-answer").addClass("marked");

    }

    function disableButtons(){
        $("#button-reading").addClass("disabled");
        $("#button-character").addClass("disabled");
    }

    function enableButtons(){
        $("#button-reading").removeClass("disabled");
        $("#button-character").removeClass("disabled");
    }

    function fill_text_with_kanji(index){
        $("#user-answer").val(current_vocab.characters[index]);
    }

    function rotateVocab(){

        if (vocabulary_list.length == 0){
            make_post("/kw/summary/", answer_correctness);
            return
        }

        $("#reviews-left").html(vocabulary_list.length);


        current_vocab = vocabulary_list.shift();
        $("#details-reading").hide();
        $("#details-character").hide();
        disableButtons();
        $("#meaning").html(current_vocab.meaning);
        $("#us-id").val(current_vocab.user_specific_id);

        $("#kana").html("");
        var i;
        for(i = 0; i < current_vocab.readings.length; i++){
            $("#kana").append(current_vocab.readings[i] + "</br>");
        }
        $("#character").html("");
        for(i = 0; i < current_vocab.characters.length; i++){
            $("#character").append(current_vocab.characters[i] + "</br>");
        }

        $("#user-answer").val("");
        $("#user-answer").css('background-color', 'white');
        $("#user-answer").focus();

    }

    $(document).keypress(function(e){
    if (e.which == 13)
    {
        $("#check").click();
    }
    if($("#user-answer").hasClass("marked"))
    {
        if (e.which == 80 || e.which == 112)
        {
            $("#button-reading").click();
        }
        else if (e.which == 75 || e.which == 107)
        {
            $("#button-character").click();
        }
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

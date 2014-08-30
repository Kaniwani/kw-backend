$(document).ready(function() {
    var input = document.getElementById("user-answer");
    var csrf_token = $("#csrf").val();//Grab CSRF token off of dummy form.
    wanakana.bind(input);
    $("#user-answer").focus();

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
    String.prototype.endsWith = function(suffix) {
        return this.indexOf(suffix, this.length - suffix.length) !== -1;
    };

    function compareAnswer(){
       var us_id;
       var answer;
       var correct;
       us_id = $("#us-id").val();
       answer = $("#user-answer").val();

       //Fixing the terminal n.
       if(answer.endsWith("n")){
           answer = answer.slice(0,-1) + "ん";
       }

       //Ensure answer is full hiragana
       if (!wanakana.isHiragana(answer) || answer == '')
       {
           nonHiraganaAnswer();
           return;
       }
       //Checking if the user's answer exists in valid readings.
       else if ($.inArray(answer, current_vocab.readings) != -1)
       {
           //Ensures this is the first time the vocab has been answered in this session, so it goes in the right
           //container(incorrect/correct)
           if($.inArray(us_id, Object.keys(answer_correctness)) == -1) {
               answer_correctness[us_id] = true;
               record_answer(us_id, true); //record answer as true
           }
           rightAnswer();
           unflagReview(us_id);
           var answer_index = $.inArray(answer, current_vocab.readings);
           fill_text_with_kanji(answer_index); //Fills the correct kanji based on the user's answers.
       }
       //answer was not in the known readings.
       else
       {
           answer_correctness[us_id] = false;
           wrongAnswer();
           record_answer(us_id, false)

       }
       enableButtons();

    }

    function unflagReview(us_id){
        $.post("/kw/unflag_review/", {user_specific_id:us_id, csrfmiddlewaretoken:csrf_token}, function(data) {
            console.log(data)
       })
    }
    function record_answer(us_id, correctness){
       //record the answer dynamically to ensure that if the session dies the user doesn't lose their half-done review session.
       $.post("/kw/record_answer/", {user_specific_id:us_id, user_correct:correctness, csrfmiddlewaretoken:csrf_token}, function(data) {
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
        $("#user-answer").css('background-color', '#00FF00');
        $("#user-answer").blur();
        $("#user-answer").addClass("marked");

    }

    function newVocab(){
        $("#user-answer").val("");
        $("#user-answer").css('background-color', 'white');
        $("#user-answer").focus();
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

        newVocab();


    }


    function enter_pressed() {
       if($("#user-answer").hasClass("marked")){
           rotateVocab();
           $("#user-answer").removeClass("marked");
       }
       else {
           compareAnswer();
       }
   }
    //Binding Enter, P, and K.
    $(document).keypress(function(e){
        if (e.which == 13) {
            enter_pressed();
        }
        if($("#user-answer").hasClass("marked")) {
            //expansion of phonetic and and char readings via keyboard.
            if (e.which == 80 || e.which == 112) {
                $("#button-reading").click();
            }
            else if (e.which == 75 || e.which == 107) {
                $("#button-character").click();
            }
        }
    });

   $("#button-reading").click(function() {
       $("#details-reading").toggle();
   });

   $("#button-character").click(function() {
       $("#details-character").toggle();
   });




});

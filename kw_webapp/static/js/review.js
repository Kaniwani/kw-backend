$(document).ready(function() {
    var input = document.getElementById("user-answer");
    var csrf_token = $("#csrf").val();//Grab CSRF token off of dummy form.
    wanakana.bind(input);

    var correct_answers = new Array();
    var incorrect_answers = new Array();

    function make_post(path, params) {
       var form = document.createElement("form");
       form.setAttribute("method", "post");
       form.setAttribute("action", path);

       for(var key in params) {
           console.log(key + " --- " + params[key]);
           if(params.hasOwnProperty(key)) {
               console.log("HAS OWN PROPERTY")
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
       console.log(form);
       form.submit();
   }


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
       else if ($.inArray(answer, current_vocab.readings) != -1) {
           if($.inArray(current_vocab.meaning, incorrect_answers) == -1) {
               correct_answers.push(current_vocab.meaning);
               correct_answers.push("|");
               console.log("Just pushed correct:" + current_vocab.meaning);
               console.log(correct_answers)
           }

           $("#user-answer").css('background-color', 'green');
           correct = true;
           $("#user-answer").addClass("marked");
           fill_text_with_kanji();
       }
       else{
           if($.inArray(current_vocab.meaning, incorrect_answers) == -1) {
               incorrect_answers.push(current_vocab.meaning);
               incorrect_answers.push("|"); //getting thrown into json removes the splits between words. Inserting a manual delimiter.
               console.log("Just Pushed incorrect: "+ current_vocab.meaning);
               console.log(incorrect_answers)
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
        $("#button-reading").addClass("disabled");
        $("#button-character").addClass("disabled");
    }
    function enableButtons(){
        console.log("IN ENABLE BUTTONS");
        $("#button-reading").removeClass("disabled");
        $("#button-character").removeClass("disabled");
    }
    function fill_text_with_kanji(){
        $("#user-answer").val(current_vocab.characters);
    }
    function rotateVocab(){
        if (vocabulary_list.length == 0){
            alert("Out of reviews!");
            var params = new Array();
            params['incorrect_answers'] = incorrect_answers;
            params['correct_answers'] = correct_answers;
            make_post("/kw/summary/", params);
            return
        }
        $("#reviews-left").html(vocabulary_list.length);
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

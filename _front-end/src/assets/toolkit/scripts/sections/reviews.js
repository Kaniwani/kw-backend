import $ from 'jquery';
import wanakana from '../vendor/wanakana.min.js';

// TODO: CACHE more $elements

const api = {

  init() {

    let correctTotal = 0;
    let answeredTotal = 0;

    var userAnswer = document.getElementById('userAnswer');
    // cache jquery objects instead of querying dom all the time
    var $userAnswer = $(userAnswer);
    var csrf_token = $("#csrf").val(); //Grab CSRF token off of dummy form.

    // only try to bind if input exists
    if (userAnswer) {
      wanakana.bind(userAnswer);
    }

    $userAnswer.focus();

    var correct_answers = [];
    var incorrect_answers = [];
    var answer_correctness = [];

    function make_post(path, params) {
      var form = document.createElement("form");
      form.setAttribute("method", "post");
      form.setAttribute("action", path);

      for (var key in params) {
        if (params.hasOwnProperty(key)) {
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

    function compareAnswer() {
      var us_id;
      var answer;
      var correct;
      var previously_wrong;
      us_id = $("#us-id").val();
      answer = $userAnswer.val();

      //Fixing the terminal n.
      if (answer.endsWith("n")) {
        answer = answer.slice(0, -1) + "ん";
      }

      //Ensure answer is full hiragana
      if (!wanakana.isHiragana(answer) || answer == '') {
        nonHiraganaAnswer();
        return;
      }

      //Checking if the user's answer exists in valid readings.
      else if ($.inArray(answer, current_vocab.readings) != -1) {
        //Ensures this is the first time the vocab has been answered in this session, so it goes in the right
        //container(incorrect/correct)
        if ($.inArray(us_id, Object.keys(answer_correctness)) == -1) {
          answer_correctness[us_id] = 1;
          previously_wrong = false;

        } else {
          previously_wrong = true;
        }
        correct = true;
        rightAnswer();
        var answer_index = $.inArray(answer, current_vocab.readings);
        fill_text_with_kanji(answer_index); //Fills the correct kanji based on the user's answers.
      }
      //answer was not in the known readings.
      else {
        if ($.inArray(us_id, Object.keys(answer_correctness)) == -1) {
          answer_correctness[us_id] = -1;
          previously_wrong = false
        } else {
          answer_correctness[us_id] -= 1;
          previously_wrong = true
        }
        wrongAnswer();
        correct = false;

      }
      record_answer(us_id, correct, previously_wrong); //record answer as true
      enableButtons();

    }

    // TODO: @djtb - use jstorage, update local storage, expires 1 week, use post only at end of review (OR ANY NAVIGATION)
    function record_answer(us_id, correctness, previously_wrong) {
      //record the answer dynamically to ensure that if the session dies the user doesn't lose their half-done review session.
      $.post("/kw/record_answer/", {
        user_specific_id: us_id,
        user_correct: correctness,
        csrfmiddlewaretoken: csrf_token,
        wrong_before: previously_wrong
      }, function(data) {
        console.log(data)
      })
    }

    function clearColors() {
      $userAnswer.removeClass('-marked -correct -incorrect -invalid');
    }

    function nonHiraganaAnswer() {
      clearColors();
      $userAnswer.addClass("-invalid");
    }

    function wrongAnswer() {
      clearColors();
      $userAnswer.addClass("-marked -incorrect");
      answeredTotal += 1;
      vocabulary_list.push(current_vocab);
    }

    function rightAnswer() {
      clearColors();
      $userAnswer.addClass("-marked -correct");
      correctTotal += 1;
      answeredTotal += 1;
    }

    function newVocab() {
      clearColors();
      $userAnswer.val("");
      $userAnswer.focus();
    }

    function disableButtons() {
      $("#detailKana .button").addClass('-disabled');
      $("#detailKanji .button").addClass('-disabled');
    }

    function enableButtons() {
      $("#detailKana .button").removeClass('-disabled');
      $("#detailKanji .button").removeClass('-disabled');
    }

    function fill_text_with_kanji(index) {
      $userAnswer.val(current_vocab.characters[index]);
    }

    function rotateVocab() {

      if (vocabulary_list.length === 0) {
        make_post("/kw/summary/", answer_correctness);
        return
      }

      $("#reviewsLeft").html(vocabulary_list.length);
      $("#reviewsDone").html(correctTotal);
      $("#reviewsCorrect").html(Math.floor((correctTotal / answeredTotal) * 100));

      current_vocab = vocabulary_list.shift();

      $(".reveal").addClass('-hidden');
      disableButtons();
      $("#meaning").html(current_vocab.meaning);
      $("#us-id").val(current_vocab.user_specific_id);

      $("#detailKana .-kana").text("");
      var i;
      for (i = 0; i < current_vocab.readings.length; i++) {
        $("#detailKana .-kana").append(current_vocab.readings[i] + "</br>");
      }
      $("#detailKanji .-kanji").text("");
      for (i = 0; i < current_vocab.characters.length; i++) {
        $("#detailKanji .-kanji").append(current_vocab.characters[i] + "</br>");
      }

      newVocab();

    }


    function enter_pressed() {
      if ($userAnswer.hasClass("-marked")) {
        rotateVocab();
        $userAnswer.removeClass("-marked");
      } else {
        compareAnswer();
      }
    }

    function keyboard_shortcuts(event) {
      if (event.which == 13) {
        event.stopPropagation();
        event.preventDefault();
        enter_pressed();
      }
      if ($userAnswer.hasClass("-marked")) {
        event.stopPropagation();
        event.preventDefault();

        //Pressing P toggles phonetic reading
        if (event.which == 80 || event.which == 112) {
          $("#detailKana .revealToggle").click();
        }
        //Pressing K toggles the actual kanji reading.
        else if (event.which == 75 || event.which == 107) {
          $("#detailKanji .revealToggle").click();
        }
        //Pressing F toggles both item info boxes.
        else if (event.which == 70 || event.which == 102) {
          $("#detailKana .revealToggle").click();
          $("#detailKanji .revealToggle").click();
        }
      }
    }

    function null_out(event) {
      event.preventDefault();
    }

    $userAnswer.on("keypress", keyboard_shortcuts);

    $("#submitAnswer").click(function() {
      enter_pressed();
    });

  }

};

export default api;

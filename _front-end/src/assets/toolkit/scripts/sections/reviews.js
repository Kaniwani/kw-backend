import wanakana from '../vendor/wanakana.min';
// simpleStorage exposed via webpack from page header CDN <script>

// cache jquery objects instead of querying dom all the time
let remainingVocab = simpleStorage.get('KW_reviewList'),
    CSRF = $("#csrf").val(), //Grab CSRF token off of dummy form.
    currentVocab,
    correctTotal = 0,
    answeredTotal = 0,
    answerCorrectness = [],
    $reviewsLeft = $("#reviewsLeft"),
    $meaning = $('#meaning'),
    $userID = $('#us-id'),
    $reviewsDone = $('#reviewsDone'),
    $reviewsCorrect = $('#reviewsCorrect'),
    $reveal = $('.reveal'),
    $userAnswer = $('#userAnswer'),
    $detailKana = $('#detailKana'),
    $detailKanji = $('#detailKanji');

function updateKanaKanjiDetails() {
  $detailKana.kana.html(currentVocab.readings.map( reading => `${reading} </br>` ));
  $detailKanji.kanji.html(currentVocab.characters.map( kanji => `${kanji} </br>` ));
}

function make_post(path, params) {
  var form = document.createElement("form");
  form.setAttribute("method", "post");
  form.setAttribute("action", path);
  form.setAttribute("class", '_visuallyhidden');

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
  let csrf_field = document.createElement("input");
  csrf_field.setAttribute("name", "csrfmiddlewaretoken");
  csrf_field.setAttribute("value", CSRF);
  form.appendChild(csrf_field);
  document.body.appendChild(form);
  form.submit();
}

String.prototype.endsWith = function(suffix) {
  return this.indexOf(suffix, this.length - suffix.length) !== -1;
};

function init() {
  // set initial values
  $reviewsLeft.text(remainingVocab.length)
  currentVocab = remainingVocab.shift();
  $meaning.html(currentVocab.meaning);
  $userID.val(currentVocab.user_specific_id);

  $detailKana.kana = $detailKana.find('.-kana');
  $detailKanji.kanji = $detailKanji.find('.-kanji');

  updateKanaKanjiDetails();

  // only try to bind IME if input exists
  if ($userAnswer) {
    wanakana.bind($userAnswer.get(0));
  }

  $userAnswer.on("keypress", handleShortcuts);

    $("#submitAnswer").click(function() {
      enterPressed();
    });

  $userAnswer.focus();
}

function compareAnswer() {
  let correct,
      previously_wrong,
      currentUserID = $userID.val(),
      answer = $userAnswer.val();

  //Fixing the terminal n.
  if (answer.endsWith('n')) {
    answer = answer.slice(0, -1) + 'ん';
  }

  //Ensure answer is full hiragana
  if (!wanakana.isHiragana(answer) || answer === '') {
    return nonHiraganaAnswer();
  }

  //Checking if the user's answer exists in valid readings.
  else if ($.inArray(answer, currentVocab.readings) != -1) {
    //Ensures this is the first time the vocab has been answered in this session, so it goes in the right
    //container(incorrect/correct)
    if ($.inArray(currentUserID, Object.keys(answerCorrectness)) == -1) {
      answerCorrectness[currentUserID] = 1;
      previously_wrong = false;

    } else {
      previously_wrong = true;
    }
    correct = true;
    rightAnswer();
    let answer_index = $.inArray(answer, currentVocab.readings);
    fill_text_with_kanji(answer_index); //Fills the correct kanji based on the user's answers.
  }
  //answer was not in the known readings.
  else {
    if ($.inArray(currentUserID, Object.keys(answerCorrectness)) == -1) {
      answerCorrectness[currentUserID] = -1;
      previously_wrong = false
    } else {
      answerCorrectness[currentUserID] -= 1;
      previously_wrong = true
    }
    wrongAnswer();
    correct = false;

  }
  recordAnswer(currentUserID, correct, previously_wrong); //record answer as true
  enableButtons();
}

 // TODO: @djtb - use storage, update local storage, expires 1 week, use post only at end of review (OR ANY NAVIGATION)
function recordAnswer(us_id, correctness, previously_wrong) {
  //record the answer dynamically to ensure that if the session dies the user doesn't lose their half-done review session.
  // TODO: @djtb record in a localStorage list instead, post that list at review end.
  // reviewcount probably needs to be in localStorage too so it can be updated, also so other parts of site can access it (so a disconnect and reconnect sees the mid-review count in title bar (from localstorage) for example).
  $.post("/kw/record_answer/", {
    user_specific_id: us_id,
    user_correct: correctness,
    csrfmiddlewaretoken: CSRF,
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
  remainingVocab.push(currentVocab);
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
  $detailKana.find('.button').addClass('-disabled');
  $detailKanji.find('.button').addClass('-disabled');
}

function enableButtons() {
  $detailKana.find('.button').removeClass('-disabled');
  $detailKanji.find('.button').removeClass('-disabled');
}

function fill_text_with_kanji(index) {
  $userAnswer.val(currentVocab.characters[index]);
}

function rotateVocab() {

  if (remainingVocab.length === 0) {
    return make_post("/kw/summary/", answerCorrectness);
  }

  $reviewsLeft.html(remainingVocab.length);
  $reviewsDone.html(correctTotal);
  $reviewsCorrect.html(Math.floor((correctTotal / answeredTotal) * 100));

  currentVocab = remainingVocab.shift();

  $reveal.addClass('-hidden');
  disableButtons();
  $meaning.html(currentVocab.meaning);
  $userID.val(currentVocab.user_specific_id);

  updateKanaKanjiDetails();
  newVocab();
}

function enterPressed() {
  if ($userAnswer.hasClass("-marked")) {
    rotateVocab();
    $userAnswer.removeClass("-marked");
  } else {
    compareAnswer();
  }
}

function handleShortcuts(event) {
  if (event.which == 13) {
    event.stopPropagation();
    event.preventDefault();
    enterPressed();
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



const api = {
  init: init
};

export default api;

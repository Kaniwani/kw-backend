import wanakana from '../vendor/wanakana.min';
import { revealToggle } from '../components/revealToggle';

//Grab CSRF token off of dummy form.
const CSRF = $('#csrf').val();

let KW,
    currentVocab,
    remainingVocab,
    startCount,
    correctTotal = 0,
    answeredTotal = 0,
    answerCorrectness = [],
    $reviewsLeft = $('#reviewsLeft'),
    $meaning = $('#meaning'),
    $streakIcon = $('.streak > .icon'),
    $ignoreButton = $('#ignoreAnswer'),
    $userID = $('#us-id'),
    $reviewsDone = $('#reviewsDone'),
    $reviewsCorrect = $('#reviewsCorrect'),
    $reveal = $('.reveal'),
    $answerForm = $('.answerForm'),
    $userAnswer = $('#userAnswer'),
    $detailKana = $('#detailKana'),
    $submitButton = $('#submitAnswer'),
    $detailKanji = $('#detailKanji'),
    $progressBar = $('.progress-bar > .value');

function init() {
  // if not on reviews page do nothing
  if (!/review/.test(window.location.pathname)) return;

  // set initial values
  KW = simpleStorage.get('KW');
  remainingVocab = window.KW.sessionVocab;
  startCount = remainingVocab.length;

  console.log('Settings:', KW.settings);

  $reviewsLeft.text(startCount - 1)
  currentVocab = remainingVocab.shift();
  $userID.val(currentVocab.user_specific_id);

  $detailKana.kana = $detailKana.find('.-kana');
  $detailKanji.kanji = $detailKanji.find('.-kanji');

  updateKanaKanjiDetails();
  updateStreak();

  // event listeners
  wanakana.bind($userAnswer.get(0));
  $userAnswer.keypress(handleShortcuts);

  // rotate or record on 'submit'
  $submitButton.click(enterPressed);
  $answerForm.submit(enterPressed);
  $ignoreButton.click(() => rotateVocab({ignored: true}));

  // ask a question
  $meaning.html(currentVocab.meaning);
  $userAnswer.focus();
}

function updateStreak() {
  let streak = currentVocab.streak;
  let iconClass = 'icon ' + (streak > 8 ? 'i-burned' :
                             streak > 7 ? 'i-enlightened' :
                             streak > 5 ? 'i-master' :
                             streak > 2 ? 'i-guru'
                                        : 'i-apprentice');

  $streakIcon.attr('class', iconClass);
  $streakIcon.closest('.streak').attr('data-hint', iconClass.slice(7));
}

function updateKanaKanjiDetails() {
  $detailKana.kana.html(currentVocab.readings.map(reading => `${reading} </br>`));
  $detailKanji.kanji.html(currentVocab.characters.map(kanji => `${kanji} </br>`));
}

function makePost(path, params) {
  var form = document.createElement('form');
  form.setAttribute('method', 'post');
  form.setAttribute('action', path);
  form.setAttribute('class', '_visuallyhidden');

  for (var key in params) {
    if (params.hasOwnProperty(key)) {
      var hiddenField = document.createElement('input');
      hiddenField.setAttribute('type', 'hidden');
      hiddenField.setAttribute('name', key);
      hiddenField.setAttribute('value', params[key]);

      form.appendChild(hiddenField);
    }
  }
  //CSRF hackery.
  let csrf_field = document.createElement('input');
  csrf_field.setAttribute('name', 'csrfmiddlewaretoken');
  csrf_field.setAttribute('value', CSRF);
  form.appendChild(csrf_field);
  document.body.appendChild(form);
  form.submit();
}

String.prototype.endsWith = function(suffix) {
  return this.indexOf(suffix, this.length - suffix.length) !== -1;
};


function compareAnswer() {
  let answer = $userAnswer.val();

  if(answer === '') return;
  console.log('Comparing', answer, 'with vocab item:', currentVocab.meaning);

  //Fixing the terminal n.
  if (answer.endsWith('n')) {
    answer = answer.slice(0, -1) + 'ん';
  }

  //Ensure answer is full hiragana
  if (!wanakana.isHiragana(answer)) {
    return nonHiraganaAnswer();
  }

  //Checking if the user's answer exists in valid readings.
  if ($.inArray(answer, currentVocab.readings) != -1) {
    markRight();
    //Fills the correct kanji into the input field based on the user's answers
    $userAnswer.val(currentVocab.characters[currentVocab.readings.indexOf(answer)]);
    processAnswer({correct: true});
    if (KW.settings.autoAdvanceCorrect) setTimeout(() => enterPressed(), 800);
  }
  //answer was not in the known readings.
  else {
    markWrong();
    // don't processAnswer() here
    // wait for submission or ignore answer - which is handled by event listeners for submit/enter
    if (KW.settings.showCorrectOnFail) revealAnswers();
  }

  enableButtons();
}

function processAnswer({correct} = {}) {
  let previouslyWrong,
      currentUserID = $userID.val();

  if (correct === true) {
    // Ensures this is the first time the vocab has been answered in this session, so it goes in the right container(incorrect/correct)
    if ($.inArray(currentUserID, Object.keys(answerCorrectness)) == -1) {
      answerCorrectness[currentUserID] = 1;
      previouslyWrong = false;
    } else {
      previouslyWrong = true;
    }

    answeredTotal += 1;
    correctTotal += 1;
    updateProgressBar(correctTotal / startCount * 100);

  } else if (correct === false) {
    if ($.inArray(currentUserID, Object.keys(answerCorrectness)) == -1) {
      answerCorrectness[currentUserID] = -1;
      previouslyWrong = false
    } else {
      answerCorrectness[currentUserID] -= 1;
      previouslyWrong = true
    }

    answeredTotal += 1;
    remainingVocab.push(currentVocab);
  }

  recordAnswer(currentUserID, correct, previouslyWrong); // record on server
}

function recordAnswer(userID, correctness, previouslyWrong) {
  $.post('/kw/record_answer/', {
      user_specific_id: userID,
      user_correct: correctness,
      csrfmiddlewaretoken: CSRF,
      wrong_before: previouslyWrong
    })
    .always(res => {
      console.log(res);
    });
}

function clearColors() {
  $userAnswer.removeClass('-marked -correct -incorrect -invalid');
}

function nonHiraganaAnswer() {
  clearColors();
  $userAnswer.addClass('-invalid');
}

function markWrong() {
  clearColors();
  $userAnswer.addClass('-marked -incorrect');
  $streakIcon.addClass('-marked');
  $ignoreButton.removeClass('-hidden');
}

function markRight() {
  clearColors();
  $userAnswer.addClass('-marked -correct');
  $streakIcon.addClass('-marked');
}

function updateProgressBar(percent) {
  $progressBar.css('width', percent + '%');
}

function resetAnswerField() {
  clearColors();
  updateStreak();
  $userAnswer.val('');
  $userAnswer.focus();
}

function disableButtons() {
  $reveal.addClass('-hidden');
  $ignoreButton.addClass('-hidden');
  $detailKanji.find('.button').addClass('-disabled');
  $detailKana.find('.button').addClass('-disabled');
}

function enableButtons() {
  $detailKanji.find('.button').removeClass('-disabled');
  $detailKana.find('.button').removeClass('-disabled');
}

function revealAnswers({kana, kanji} = {}) {
  if (!!kana) revealToggle($detailKana.find('.button'));
  else if (!!kanji) revealToggle($detailKanji.find('.button'));
  else {
    revealToggle($detailKana.find('.button'));
    revealToggle($detailKanji.find('.button'));
  }
}

function rotateVocab({ignored = false, correct = false} = {}) {
  console.log('ignored:', ignored);

  if (ignored) {
    // put ignored answer back onto end of review queue
    remainingVocab.push(currentVocab);
  }

  if (remainingVocab.length === 0) {
    console.log('Summary post data', answerCorrectness);
    return makePost('/kw/summary/', answerCorrectness);
  }

  currentVocab = remainingVocab.shift();

  if (correct) {
    $reviewsLeft.html(remainingVocab.length);
    $reviewsDone.html(correctTotal);
  }

  // guard against 0 / 0 (when first answer ignored)
  let percentCorrect = Math.floor((correctTotal / answeredTotal) * 100) || 0;
  console.log(`
    remain length: ${remainingVocab.length},
    vocab: ${remainingVocab.map(x => x.meaning.split(',')[0])},
    correcttotal: ${correctTotal},
    answertotal: ${answeredTotal},
    correct: ${percentCorrect}`
  );
  $reviewsCorrect.html(percentCorrect);
  $meaning.html(currentVocab.meaning);
  $userID.val(currentVocab.user_specific_id);

  disableButtons();
  updateKanaKanjiDetails();
  resetAnswerField();
}

function enterPressed(event) {
  if (event != null) {
    event.stopPropagation();
    event.preventDefault();
  }
  console.log(event);
  if ($userAnswer.hasClass('-marked')) {
    if ($userAnswer.hasClass('-correct')) {
      rotateVocab({correct: true});
    } else if($userAnswer.hasClass('-incorrect')) {
      processAnswer({correct: false});
      rotateVocab({correct: false});
    }
  } else {
    compareAnswer();
  }
}

function handleShortcuts(event) {
  if (event.which == 13) {
    event.stopPropagation();
    event.preventDefault();
    enterPressed(null);
  }
  if ($userAnswer.hasClass('-marked')) {
    event.stopPropagation();
    event.preventDefault();

    //Pressing P toggles phonetic reading
    if (event.which == 80 || event.which == 112) {
      revealAnswers({kana: true});
    }
    //Pressing K toggles the actual kanji reading.
    else if (event.which == 75 || event.which == 107) {
      revealAnswers({kanji: true});
    }
    //Pressing F toggles both item info boxes.
    else if (event.which == 70 || event.which == 102) {
      revealAnswers();
    }
    //Pressing I ignores answer when input is marked incorrect
    else if (event.which == 73 || event.which == 105) {
      if ($userAnswer.hasClass('-incorrect')) rotateVocab({ignored: true});
    }
  }
}

const api = {
  init: init
};

export default api;

import wanakana from '../vendor/wanakana.min';
import { revealToggle } from '../components/revealToggle';

// cache jquery objects instead of querying dom all the time
let CSRF = $('#csrf').val(), //Grab CSRF token off of dummy form.
  userSettings,
  remainingVocab,
  currentVocab,
  startCount,
  correctTotal = 0,
  answeredTotal = 0,
  answerCorrectness = [],
  $reviewsLeft = $('#reviewsLeft'),
  $meaning = $('#meaning'),
  $streakIcon = $('.streak > .icon'),
  $userID = $('#us-id'),
  $reviewsDone = $('#reviewsDone'),
  $reviewsCorrect = $('#reviewsCorrect'),
  $reveal = $('.reveal'),
  $answerForm = $('.answerForm'),
  $userAnswer = $('#userAnswer'),
  $detailKana = $('#detailKana'),
  $submitAnswer = $('#submitAnswer'),
  $detailKanji = $('#detailKanji'),
  $progressBar = $('.progress-bar > .value');

function init() {
  // if not on reviews page do nothing
  if (!/review/.test(window.location.pathname)) return;

  // map python True/False passed from view as strings to JS true/false booleans
  window.KWusersettings = strToBoolean(window.KWuserSettings);
  function strToBoolean(o) {
    for (let k of Object.keys(o)) {
      let v = o[k];
      o[k] = (v === 'True' ? true : false);
    }
  }

  // set initial values
  remainingVocab = window.KWsessionVocab;
  startCount = remainingVocab.length;

  console.log('\nLength:', startCount);

  $reviewsLeft.text(startCount)
  currentVocab = remainingVocab.shift();
  console.log(currentVocab);
  $userID.val(currentVocab.user_specific_id);

  $detailKana.kana = $detailKana.find('.-kana');
  $detailKanji.kanji = $detailKanji.find('.-kanji');

  updateKanaKanjiDetails();
  updateStreak();

  // event listeners
  wanakana.bind($userAnswer.get(0));
  $userAnswer.keypress(handleShortcuts);

  // rotate or record on 'submit'
  $submitAnswer.click(enterPressed);
  $answerForm.submit(enterPressed);

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

  $streakIcon.attr('class', iconClass).attr('title', iconClass.slice(2));
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
  let correct,
    previouslyWrong,
    currentUserID = $userID.val(),
    answer = $userAnswer.val();

  console.log('Comparing', answer, 'with vocab item:', currentVocab.meaning);

  //Fixing the terminal n.
  if (answer.endsWith('n')) {
    answer = answer.slice(0, -1) + 'ん';
  }

  //Ensure answer is full hiragana
  if (!wanakana.isHiragana(answer)) {
    return nonHiraganaAnswer();
  } else if(answer === '') {
    return;
  }

  //Checking if the user's answer exists in valid readings.
  else if ($.inArray(answer, currentVocab.readings) != -1) {
    //Ensures this is the first time the vocab has been answered in this session, so it goes in the right
    //container(incorrect/correct)
    if ($.inArray(currentUserID, Object.keys(answerCorrectness)) == -1) {
      answerCorrectness[currentUserID] = 1;
      previouslyWrong = false;

    } else {
      previouslyWrong = true;
    }
    correct = true;
    rightAnswer();
    var answerIndex = $.inArray(answer, currentVocab.readings);
    //Fills the correct kanji into the input field based on the user's answers
    $userAnswer.val(currentVocab.characters[currentVocab.readings.indexOf(answer)]);
  }
  //answer was not in the known readings.
  else {
    if ($.inArray(currentUserID, Object.keys(answerCorrectness)) == -1) {
      answerCorrectness[currentUserID] = -1;
      previouslyWrong = false
    } else {
      answerCorrectness[currentUserID] -= 1;
      previouslyWrong = true
    }
    wrongAnswer();
    correct = false;
  }

  if (!correct && userSettings.showCorrectOnFail) revealAnswers();
  if (correct && userSettings.autoAdvanceCorrect) setTimeout(() => enterPressed(), 800);

  recordAnswer(currentUserID, correct, previouslyWrong); //record answer as true
  enableButtons();
}

function recordAnswer(userID, correctness, previouslyWrong) {
  $.post('/kw/record_answer/', {
      user_specific_id: userID,
      user_correct: correctness,
      csrfmiddlewaretoken: CSRF,
      wrong_before: previouslyWrong
    })
    .done(() => {
      // anything need
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

function wrongAnswer() {
  clearColors();
  $userAnswer.addClass('-marked -incorrect');
  $streakIcon.addClass('-marked');
  answeredTotal += 1;
  remainingVocab.push(currentVocab);
}

function rightAnswer() {
  clearColors();
  $userAnswer.addClass('-marked -correct');
  $streakIcon.addClass('-marked');
  correctTotal += 1;
  answeredTotal += 1;
  updateProgressBar(correctTotal / startCount * 100);
}

function updateProgressBar(percent) {
  $progressBar.css('width', percent + '%');
}

function newVocab() {
  clearColors();
  updateStreak();
  $userAnswer.val('');
  $userAnswer.focus();
}

function disableButtons() {
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

function rotateVocab() {
  $reviewsLeft.html(remainingVocab.length);
  $reviewsDone.html(correctTotal);
  $reviewsCorrect.html(Math.floor((correctTotal / answeredTotal) * 100));

  if (remainingVocab.length === 0) {
    console.log('Summary post data', answerCorrectness);
    return makePost('/kw/summary/', answerCorrectness);
  }

  currentVocab = remainingVocab.shift();
  $reveal.addClass('-hidden');
  $meaning.html(currentVocab.meaning);
  $userID.val(currentVocab.user_specific_id);

  disableButtons();
  updateKanaKanjiDetails();
  newVocab();
}

function enterPressed(event) {
  if (event != null) {
    event.stopPropagation();
    event.preventDefault();
  }
  $userAnswer.hasClass('-marked') ? rotateVocab() : compareAnswer();
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
  }
}

const api = {
  init: init
};

export default api;
